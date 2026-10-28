// Deterministic inward-normal wall sampling on closed, consistently wound STLs.
// Ray/triangle BVH; samples are interior to faces, not at shared edges.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <vector>
using namespace std;
struct V {double x,y,z; double operator[](int i)const{return i==0?x:i==1?y:z;} V operator+(V b)const{return{x+b.x,y+b.y,z+b.z};} V operator-(V b)const{return{x-b.x,y-b.y,z-b.z};} V operator*(double s)const{return{x*s,y*s,z*s};}};
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;} V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
struct Tri{V a,b,c,n,mid,lo,hi;double area;};struct Node{V lo,hi;int start,end,left=-1,right=-1;};
vector<Tri> ts;vector<int> ids;vector<Node> tree;
V mn(V a,V b){return{min(a.x,b.x),min(a.y,b.y),min(a.z,b.z)};}V mx(V a,V b){return{max(a.x,b.x),max(a.y,b.y),max(a.z,b.z)};}
int build(int s,int e){Node q;q.start=s;q.end=e;q.lo={1e10,1e10,1e10};q.hi={-1e10,-1e10,-1e10};for(int i=s;i<e;i++){q.lo=mn(q.lo,ts[ids[i]].lo);q.hi=mx(q.hi,ts[ids[i]].hi);}int index=tree.size();tree.push_back(q);if(e-s>8){V d=q.hi-q.lo;int ax=d.y>d.x?1:0;if(d.z>d[ax])ax=2;int mid=(s+e)/2;nth_element(ids.begin()+s,ids.begin()+mid,ids.begin()+e,[ax](int a,int b){return ts[a].mid[ax]<ts[b].mid[ax];});int l=build(s,mid),r=build(mid,e);tree[index].left=l;tree[index].right=r;}return index;}
bool bbox(V o,V d,const Node&q,double best){double lo=0,hi=best;for(int k=0;k<3;k++){if(abs(d[k])<1e-12){if(o[k]<q.lo[k]-1e-8||o[k]>q.hi[k]+1e-8)return false;}else{double a=(q.lo[k]-o[k])/d[k],b=(q.hi[k]-o[k])/d[k];if(a>b)swap(a,b);lo=max(lo,a);hi=min(hi,b);if(lo>hi)return false;}}return true;}
double triHit(V o,V d,const Tri&t){V e=t.b-t.a,f=t.c-t.a,h=cross(d,f);double det=dot(e,h);if(abs(det)<1e-12)return 1e10;V s=o-t.a;double u=dot(s,h)/det;if(u< -1e-8||u>1+1e-8)return 1e10;V q=cross(s,e);double v=dot(d,q)/det;if(v< -1e-8||u+v>1+1e-8)return 1e10;double z=dot(f,q)/det;return z>1e-5?z:1e10;}
void ray(int ni,V o,V d,int own,double &best,int &face){const Node&q=tree[ni];if(!bbox(o,d,q,best))return;if(q.left<0){for(int i=q.start;i<q.end;i++){int j=ids[i];if(j==own)continue;double z=triHit(o,d,ts[j]);if(z<best){best=z;face=j;}}}else{ray(q.left,o,d,own,best,face);ray(q.right,o,d,own,best,face);}}
void vec(V a){cout<<'['<<a.x<<','<<a.y<<','<<a.z<<']';}
int main(int argc,char**argv){if(argc<2)return 1;ifstream f(argv[1],ios::binary);char head[80];uint32_t n;f.read(head,80);f.read((char*)&n,4);for(uint32_t i=0;i<n;i++){float q[12];uint16_t attr;f.read((char*)q,48);f.read((char*)&attr,2);Tri t;t.a={q[3],q[4],q[5]};t.b={q[6],q[7],q[8]};t.c={q[9],q[10],q[11]};V c=cross(t.b-t.a,t.c-t.a);double length=sqrt(dot(c,c));if(length<1e-12)continue;t.n=c*(1/length);t.area=length/2;t.mid=(t.a+t.b+t.c)*(1./3);t.lo=mn(t.a,mn(t.b,t.c));t.hi=mx(t.a,mx(t.b,t.c));ts.push_back(t);}for(int i=0;i<(int)ts.size();i++)ids.push_back(i);build(0,ids.size());cout<<setprecision(7)<<"{\"thin_samples\":[";bool first=true;uint64_t total=0,thin=0,miss=0;double bins[7]={},area=0;double limits[]={.4,.8,1.2,1.6,1.8,2.,1e10};for(int i=0;i<(int)ts.size();i++){const Tri&t=ts[i];int ns=max(2,min(180,(int)ceil(sqrt(t.area*2))));int samples=ns*(ns+1)/2;for(int a=0;a<ns;a++)for(int b=0;b<ns-a;b++){double u=(a+1./3)/ns,v=(b+1./3)/ns;V p=t.a+(t.b-t.a)*u+(t.c-t.a)*v;V dir=t.n*(-1);double distance=1e10;int face=-1;ray(0,p+dir*.002,dir,i,distance,face);total++;double w=t.area/samples;area+=w;if(face<0){miss++;continue;}distance+=.002;for(int k=0;k<7;k++)if(distance<limits[k]){bins[k]+=w;break;}if(distance<1.8){thin++;if(!first)cout<<',';first=false;cout<<"{\"p\":";vec(p);cout<<",\"n\":";vec(t.n);cout<<",\"end\":";vec(p+dir*distance);cout<<",\"end_n\":";vec(ts[face].n);cout<<",\"t\":"<<distance<<",\"weight\":"<<w<<",\"tri\":"<<i<<'}';}}}cout<<"],\"sample_count\":"<<total<<",\"miss_count\":"<<miss<<",\"thin_count\":"<<thin<<",\"sampled_surface_area_mm2\":"<<area<<",\"area_bins_lt_0_4_0_8_1_2_1_6_1_8_2_rest_mm2\":[";for(int i=0;i<7;i++){if(i)cout<<',';cout<<bins[i];}cout<<"]}\n";}
