"""M20 measured LiDAR grid (true simulation pose); no SLAM/ROS equivalence claim."""
import heapq
import math
import numpy as np
from scipy import ndimage
import mujoco

ENVIRONMENT_GROUPS=np.array([1,0,0,0,0,0],dtype=np.uint8)

def beam_directions(azimuth, elevation):
    az,el=np.broadcast_arrays(azimuth,elevation)
    return np.stack((np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)),axis=-1)

def raycast(model,data,origin,directions,max_range=7.0):
    directions=np.ascontiguousarray(directions,dtype=np.float64).reshape(-1,3)
    directions/=np.linalg.norm(directions,axis=1)[:,None]
    ids=np.full(len(directions),-1,dtype=np.int32)
    distances=np.full(len(directions),-1.0,dtype=np.float64)
    # mj_multiRay's cutoff culls GEOMS, not individual ray lengths. A plane
    # anchored at world zero was incorrectly culled when the robot drove >5 m
    # away. Disable that coarse cull; enforce the sensor range on hits below.
    mujoco.mj_multiRay(model,data,np.asarray(origin,dtype=np.float64),directions.ravel(),
                     ENVIRONMENT_GROUPS,1,-1,ids,distances,None,len(ids),1e6)
    valid=(ids>=0)&(distances>=0)&(distances<=max_range)&np.isfinite(distances)
    points=np.asarray(origin)+directions[valid]*distances[valid,None]
    return points,distances,ids,valid

def normalized_cost(slope_rad,roughness_m,step_m):
    return np.clip(0.4*np.clip(slope_rad/np.deg2rad(30),0,1)+
                   0.3*np.clip(roughness_m/0.04,0,1)+0.3*np.clip(step_m/0.14,0,1),0,1)

class M20Map:
    def __init__(self,resolution=0.03,bounds=(-1.2,6.0,-3.0,3.0)):
        self.resolution=resolution
        self.bounds=bounds
        xmin,xmax,ymin,ymax=bounds
        self.xs=np.arange(xmin+resolution/2,xmax,resolution)
        self.ys=np.arange(ymin+resolution/2,ymax,resolution)
        self.shape=(len(self.ys),len(self.xs))
        self.count=np.zeros(self.shape,dtype=np.int64)
        self.sum=np.zeros(self.shape)
        self.sumsq=np.zeros(self.shape)
        self.peak=np.full(self.shape,-np.inf)
        self.mean=np.full(self.shape,np.nan)
        # Retain exact measured x coordinates in 2 cm height bands. Grid-cell
        # boundaries alone can shift a step lip by a full cell (5 cm here).
        self.step_min_x=np.full((16,*self.shape),np.inf)
        self.cost=np.full(self.shape,0.85)
        self.slope=np.zeros(self.shape)
        self.roughness=np.zeros(self.shape)
        self.step=np.zeros(self.shape)
        self.unsafe=np.zeros(self.shape,bool)
        self.inflated=self.unsafe.copy()
        xx,yy=np.meshgrid(self.xs,self.ys)
        self.targets=np.column_stack((xx.ravel(),yy.ravel(),np.zeros(xx.size)))
        self.scan_index=0;self.total_hits=0

    @property
    def known(self): return self.count>0

    def cell(self,xy):
        x,y=xy
        return (int(math.floor((y-self.bounds[2])/self.resolution)),int(math.floor((x-self.bounds[0])/self.resolution)))

    def inside(self,rc): return 0<=rc[0]<self.shape[0] and 0<=rc[1]<self.shape[1]

    def xy(self,rc): return np.array((self.xs[rc[1]],self.ys[rc[0]]))

    def integrate(self,points):
        if len(points)==0:return
        points=np.asarray(points)
        points=points[np.isfinite(points).all(axis=1)]
        rc=np.floor((points[:,:2]-[self.bounds[0],self.bounds[2]])/self.resolution).astype(int)
        valid=(rc[:,0]>=0)&(rc[:,0]<self.shape[1])&(rc[:,1]>=0)&(rc[:,1]<self.shape[0])
        c,r=rc[valid].T;z=points[valid,2]
        np.add.at(self.count,(r,c),1)
        np.add.at(self.sum,(r,c),z)
        np.add.at(self.sumsq,(r,c),z*z)
        np.maximum.at(self.peak,(r,c),z)
        height_bin=np.clip(np.floor(z/.02).astype(int),0,15)
        np.minimum.at(self.step_min_x,(height_bin,r,c),points[valid,0])
        self.mean[self.known]=self.sum[self.known]/self.count[self.known]

    def update_cost(self,climb=False):
        known=self.known
        if not known.any():return
        # Nearest measured surface fills metric stencils only; unknown remains blocked.
        ind=ndimage.distance_transform_edt(~known,return_distances=False,return_indices=True)
        z=self.mean[tuple(ind)]
        gy,gx=np.gradient(z,self.resolution)
        self.slope=np.arctan(np.hypot(gx,gy))
        local_mean=ndimage.uniform_filter(z,size=3,mode="nearest")
        self.roughness=np.sqrt(np.maximum(0,ndimage.uniform_filter(z*z,size=3,mode="nearest")-local_mean**2))
        self.step=ndimage.maximum_filter(z,size=3)-ndimage.minimum_filter(z,size=3)
        self.cost=normalized_cost(self.slope,self.roughness,self.step)
        # Height/step rejection retains tall obstacles rather than deleting all z>0.35.
        self.unsafe=known&((self.step>0.145)|((self.peak-local_mean)>0.145))
        radius=0.70  # Measured M20 footprint (~0.50 m circumscribed) + safety margin.
        distance=ndimage.distance_transform_edt(~self.unsafe)*self.resolution
        self.inflated=distance<=radius
        self.cost+=.8*np.clip((1.05-distance)/1.05,0,1)
        self.cost[~known]=0.85

    def scan(self,model,data,climb=False):
        origin=data.site('recon_lidar').xpos.copy()
        # Interleaved dense ground-directed pattern: 50 Hz integration, one full
        # lattice sweep each 0.32 s. Individual rays intersect actual geometry.
        targets=self.targets[self.scan_index%16::16]
        self.scan_index+=1
        delta=targets-origin
        norms=np.linalg.norm(delta,axis=1)
        selected=(norms<5.0)&(norms>.05)
        points,*_=raycast(model,data,origin,delta[selected],5.0)
        self.integrate(points);self.total_hits+=len(points)
        if self.scan_index%5==0:self.update_cost(climb)
        return len(points)

    def detect_step(self,position,ground_height=0.,conservative_lip=False):
        # Detect a broad low terrace from measured cells, excluding inflated tall hazards.
        known=self.known
        mask=known & (self.mean>ground_height+.035) & (self.peak<ground_height+.14) & ~self.inflated
        xx,yy=np.meshgrid(self.xs,self.ys)
        mask &= (xx>position[0]+.15)&(np.abs(yy)<.75)
        labels,n=ndimage.label(mask)
        best=None
        for label in range(1,n+1):
            cells=labels==label
            if cells.sum()*self.resolution**2<.10:continue
            if np.ptp(yy[cells])<.45:continue
            lip=float(xx[cells].min()-self.resolution/2)
            if conservative_lip:
                bands=np.arange(16)*.02>=ground_height+.035
                measured=self.step_min_x[bands][:,cells]
                if np.isfinite(measured).any():lip=float(np.min(measured))
            height=float(np.median(self.peak[cells]))
            if best is None or lip<best[0]:best=(lip,height)
        return best

    def height_at(self,xy):
        rc=self.cell(xy)
        return float(self.mean[rc]) if self.inside(rc) and self.known[rc] else 0.

    def save(self,path,path_xy=()):
        np.savez_compressed(path,mean=self.mean,count=self.count,peak=self.peak,cost=self.cost,
            slope=self.slope,roughness=self.roughness,step=self.step,unsafe=self.unsafe,
            inflated=self.inflated,step_min_x=self.step_min_x,bounds=self.bounds,resolution=self.resolution,path=np.asarray(path_xy))

def astar(grid,start,goal):
    """8-neighbor A*, strict unknown blocking and no diagonal corner cutting."""
    blocked=grid.inflated|~grid.known
    if not grid.inside(start) or not grid.inside(goal) or blocked[goal] or blocked[start]:return []
    queue=[(0.0,start)];score={start:0.0};parent={};closed=set()
    while queue:
        _,current=heapq.heappop(queue)
        if current in closed:continue
        if current==goal:
            path=[current]
            while current in parent:current=parent[current];path.append(current)
            return path[::-1]
        closed.add(current)
        for dr,dc in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
            nxt=(current[0]+dr,current[1]+dc)
            if not grid.inside(nxt) or blocked[nxt]:continue
            if dr and dc and (blocked[current[0]+dr,current[1]] or blocked[current[0],current[1]+dc]):continue
            new=score[current]+math.hypot(dr,dc)*(1+2*grid.cost[nxt])
            if new<score.get(nxt,math.inf):
                score[nxt]=new;parent[nxt]=current
                heuristic=math.hypot(nxt[0]-goal[0],nxt[1]-goal[1])
                heapq.heappush(queue,(new+heuristic,nxt))
    return []

def plan_route(grid,position,goal):
    start,end=grid.cell(position),grid.cell(goal)
    path=astar(grid,start,end)
    if path:return np.array([grid.xy(c) for c in path]),"goal_route"
    # Measured frontier candidates approach the goal without assuming unknown is safe.
    free=grid.known&~grid.inflated
    frontier=free&ndimage.binary_dilation(~grid.known)
    components,_=ndimage.label(free,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    label=components[start] if grid.inside(start) else 0
    if label==0:return np.empty((0,2)),"no_safe_path"
    cells=np.argwhere(frontier & (components==label))
    if len(cells):
        order=np.argsort(np.linalg.norm(np.array([grid.xy(c) for c in cells])-goal,axis=1))
        for i in order[:12]:
            candidate=tuple(cells[i])
            if np.linalg.norm(grid.xy(candidate)-position)<0.5:continue
            path=astar(grid,start,candidate)
            if path:return np.array([grid.xy(c) for c in path]),"frontier_route"
    return np.empty((0,2)),"no_safe_path"

def forward_clearance(model,data):
    # Robot-aligned 180-degree scan at bumper height, all environment geoms included.
    rot=data.body("base_link").xmat.reshape(3,3)
    origin=data.body("base_link").xpos+rot@np.array([0.42,0,-0.30])
    az=np.linspace(-np.pi/2,np.pi/2,181)
    dirs=beam_directions(az,np.zeros_like(az))@rot.T
    points,dist,ids,valid=raycast(model,data,origin,dirs,5.0)
    central=valid&(np.abs(az)<np.deg2rad(25))
    return float(np.min(dist[central])) if central.any() else 5.0

# Compatibility name retained for the supplied repository structure.
M20RosbotSLAMMapper=M20Map
ElevationMap=M20Map
