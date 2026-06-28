/*
* License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
* Created by bal-khan
*/

vec2	march(vec3 pos, vec3 dir);
vec3	camera(vec2 uv);
void	rotate(inout vec2 v, float angle);
vec3	calcNormal( in vec3 pos, float e, vec3 dir);
float	loop_circle(vec3 p);
float	circle(vec3 p, float phase);
float	sdTorus( vec3 p, vec2 t, float phase );
float	mylength(vec2 p);
float	nrand( vec2 n );

float 	t;			// time
vec3	ret_col;	// torus color
vec3	h; 			// light amount

#define I_MAX		200.
#define E			0.00001
#define FAR			15.
#define PI			3.14

void mainImage(out vec4 c_out, in vec2 f)
{
    t  = iTime*.125;
    vec3	col = vec3(0., 0., 0.);
	vec2 R = iResolution.xy,
          uv  = vec2(f-R/2.) / R.y;
	vec3	dir = camera(uv);
    vec3	pos = vec3(.0, .0, 0.0);

    pos.z = 4.5+1.5*sin(t*10.);    
    h*=0.;
    vec2	inter = (march(pos, dir));
    if (inter.y <= FAR)
        col.xyz = ret_col*(1.-inter.x*.0025);
    else
        col *= 0.;
    col += h*.005125;
    c_out =  vec4(col,1.0);
}

float	scene(vec3 p)
{  
    float	var;
    float	mind = 1e5;
    p.z += 2.;
    rotate(p.xz, 1.57-.5*iTime);
    rotate(p.yz, 1.57-.5*iTime);
    vec2 q = vec2(mix(mylength(p.xy), length(p.xy), abs(sin(iTime)) )-2.,p.z);
    var = atan(p.x,p.y);
    rotate(q, var+iTime*2.);
    q = abs(q)-.5;
    rotate(q, var*-3.+iTime*2.);
    var = cos(floor(var*6.)*.5+iTime*3. );
    ret_col = 1.-vec3(.5-var*.5, .5, .3+var*.5);
    mind = mylength(q)-.125-.1*var;
    h += vec3(.5,.8,.5)*(var!=0.?0.:1.)*vec3(1.)*.0125/(.01+(mind-var*.1)*(mind-var*.1) );
    h += vec3(.5,.8,.5)*(var!=0.?1.:0.)*vec3(1.)*.0125/(.01+mind*mind);
    
    return (mind);
}

vec2	march(vec3 pos, vec3 dir)
{
    vec2	dist = vec2(0.0, 0.0);
    vec3	p = vec3(0.0, 0.0, 0.0);
    vec2	s = vec2(0.0, 0.0);

	    for (float i = -1.; i < I_MAX; ++i)
	    {
	    	p = pos + dir * dist.y;
	        dist.x = scene(p);
	        dist.y += dist.x*.2; // makes artefacts disappear
	        if (dist.x < E || dist.y > FAR)
            {
                break;
            }
	        s.x++;
    }
    s.y = dist.y;
    return (s);
}

float	mylength(vec2 p)
{
	float	ret;
    
    p = p*p*p*p;
    p = p*p;
    ret = (p.x+p.y);
    ret = pow(ret, 1./8.);
    
    return ret;
}

// Utilities

void rotate(inout vec2 v, float angle)
{
	v = vec2(cos(angle)*v.x+sin(angle)*v.y,-sin(angle)*v.x+cos(angle)*v.y);
}

vec2	rot(vec2 p, vec2 ang)
{
	float	c = cos(ang.x);
    float	s = sin(ang.y);
    mat2	m = mat2(c, -s, s, c);
    
    return (p * m);
}

vec3	camera(vec2 uv)
{
    float		fov = 1.;
	vec3		forw  = vec3(0.0, 0.0, -1.0);
	vec3    	right = vec3(1.0, 0.0, 0.0);
	vec3    	up    = vec3(0.0, 1.0, 0.0);

    return (normalize((uv.x) * right + (uv.y) * up + fov * forw));
}

vec3 calcNormal( in vec3 pos, float e, vec3 dir)
{
    vec3 eps = vec3(e,0.0,0.0);

    return normalize(vec3(
           march(pos+eps.xyy, dir).y - march(pos-eps.xyy, dir).y,
           march(pos+eps.yxy, dir).y - march(pos-eps.yxy, dir).y,
           march(pos+eps.yyx, dir).y - march(pos-eps.yyx, dir).y ));
}