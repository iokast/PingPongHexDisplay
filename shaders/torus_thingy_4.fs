/*
* License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
*/

float 	t;

#define I_MAX		200
#define E			0.001
#define FAR			10.

#define	FUDGE
// artifactus disparatus !! (fudge needed cuz of high curvature distorsion)
//#define PHONG

vec4	march(vec3 pos, vec3 dir);
vec3	camera(vec2 uv);
vec3	calcNormal(in vec3 pos, float e, vec3 dir);
void	rotate(inout vec2 v, float angle);
float	mylength(vec2 p);
float	mylength(vec3 p);

vec3	base;
vec3	h;
vec3	volumetric;

void mainImage(out vec4 c_out, in vec2 f)
{
    h *= 0.;
    volumetric *= 0.;
    t = iTime;
    vec3	col = vec3(0., 0., 0.);
	vec2	uv  = vec2((f.x-.5*iResolution.x)/iResolution.x, (f.y-.5*iResolution.y)/iResolution.y);
	vec3	dir = camera(uv);
    vec3	pos = vec3(-.0, .0, 25.0-sin(iTime*.125)*25.*0.-21.+2.);

    vec4	inter = (march(pos, dir));

    if (inter.y == 1.)
    {
    	base = vec3(.5, .25, .8);
	    #ifdef PHONG
        // substracting a bit from the ray to get a better normal
		vec3	v = pos+(inter.w-E*10.)*dir;
        vec3	n = calcNormal(v, E, dir);
        vec3	ev = normalize(v - pos);
		vec3	ref_ev = reflect(ev, n);
        vec3	light_pos   = vec3(0.0, 0.0, 0.0);
		vec3	light_color = vec3(.0, .5, .2);
        vec3	vl = normalize( (light_pos - v) );
		float	diffuse  = max(0., dot(vl, n));
		float	specular = pow(max(0., dot(vl, ref_ev)), 10.8 );
        col.xyz = light_color * (specular) + diffuse * base;
        float	dt = 1. - dot(n, normalize(-ev) );
        col += smoothstep(.0, 1.0, dt)*vec3(.2, .7, .90);
	#else
    	col.xyz = 1.*( +vec3(.3, .4, .2)*inter.w * .3-inter.x*.1 * vec3(.15, .2, .15) );
	#endif
    	col  -= -.25 + h;
    }
    col += volumetric;
    c_out =  vec4(col, h.x);
}

float	scene(vec3 p)
{
    p.z+=sin(t*.5)*2.;
    float	balls = 1e5;
    float	lumos = 1e5;
	vec3	pr;

    vec2	q;
    
    pr = p;
    
    rotate(pr.yz , iTime*.5);
    rotate(pr.xz , iTime*1.);
        
    float	ata = atan(pr.x, pr.y)*1.+0.;
    
    q = vec2(length(pr.xy)-2., pr.z);
    
    rotate(q.xy, +iTime*2.+ata*2.);
    
    q.xy = abs(q.xy)-.25;
    
    rotate(q.xy, -iTime*2.+ata*1. );
    q.x = abs(q.x)-.25;
    rotate(q.xy, +iTime*2.+ata*8. );
    q.xy = abs(q.xy)-.051;
    balls = mylength(q)+(-.0405+sin( (ata*2.)-iTime*3.)*.0251);
    
    
    
    float	light = length(pr)-.01;

	#ifdef	FUDGE
    balls *= .5;
    #endif
    rotate(p.yx, iTime*.5);
    #ifdef	FUDGE
    lumos = length(p.y-18.)-20.1;
    h += (.251/(lumos + 10.1))*vec3(.0,.0,.5);
    lumos = length(p.y+18.)-20.1;
    h += (.251/(lumos + 10.1))*vec3(.0, .5, .0);
    volumetric += .1/(light+2.1)*vec3(.085,.105,.505);
    #else
    lumos = length(p.y-18.)-10.1;
    h += (.51/(lumos + 10.1))*vec3(.0,.0,.5);
    lumos = length(p.y+18.)-10.1;
    h += (.51/(lumos + 10.1))*vec3(.0, .5, .0);
    volumetric += .2/(light+2.1)*vec3(.085,.105,.505);
    #endif
	
    return(balls);
}

vec4	march(vec3 pos, vec3 dir)
{
    vec2	dist = vec2(0.0, 0.0);
    vec3	p = vec3(0.0, 0.0, 0.0);
    vec4	step = vec4(0.0, 0.0, 0.0, 0.0);

    for (int i = -1; i < I_MAX; ++i)
    {
    	p = pos + dir * dist.y;
        dist.x = scene(p);
        dist.y += dist.x*1.;
        // log trick by aiekick
        if (log(dist.y*dist.y/dist.x/1e5)>0. || dist.x < E || dist.y >= FAR)
        {
            if (dist.x < E)
	            step.y = 1.;
            break;
        }
        step.x++;
    }
    step.w = dist.y;
    return (step);
}

// Utilities

float	mylength(vec3 p)
{
	float	ret = 1e5;
    
    p = p*p;
    p = p*p;
    p = p*p;
    
    ret = p.x + p.y + p.z;
    ret = pow(ret, 1./8.);
    
    return ret;
}

float	mylength(vec2 p)
{
	float	ret = 1e5;
    
    p = p*p;
    p = p*p;
    p = p*p;
    
    ret = p.x + p.y;
    ret = pow(ret, 1./8.);
    
    return ret;
}

void rotate(inout vec2 v, float angle)
{
	v = vec2(cos(angle)*v.x+sin(angle)*v.y,-sin(angle)*v.x+cos(angle)*v.y);
}

vec3 calcNormal( in vec3 pos, float e, vec3 dir)
{
    vec3 eps = vec3(e,0.0,0.0);

	return normalize(vec3(
           march(pos+eps.xyy, dir).w - march(pos-eps.xyy, dir).w,
           march(pos+eps.yxy, dir).w - march(pos-eps.yxy, dir).w,
           march(pos+eps.yyx, dir).w - march(pos-eps.yyx, dir).w ));
}

vec3	camera(vec2 uv)
{
    float		fov = 1.;
	vec3		forw  = vec3(0.0, 0.0, -1.0);
	vec3    	right = vec3(1.0, 0.0, 0.0);
	vec3    	up    = vec3(0.0, 1.0, 0.0);

    return (normalize((uv.x) * right + (uv.y) * up + fov * forw));
}
