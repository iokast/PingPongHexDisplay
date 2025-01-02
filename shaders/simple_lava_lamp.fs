// https://www.shadertoy.com/view/WttyRX

float rand(int i) {  // produce some "random" numbers to vary the blobs
    return sin(float(i) * 1.64);
}

vec3 get_blob(int i, float time){
    // Blob movement parameters
    float spd = .25;
    float move_range = .5;
    // ---
    float x = float(i);    
    vec2 center = vec2(.5,.5) + .1 * vec2(rand(i),rand(i+42));    
    center += move_range * vec2(sin(spd * time * rand(i+2)) * rand(i + 56), -sin(spd * time) * rand(i*9));
    float radius = .1 * abs(rand(i+3));    
    return vec3(center.xy,radius);
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{    
    // Shading parameters
    vec3 blob_color_center = vec3(0,0,1); // blue center
    vec3 blob_color_edge = vec3(1,0,1); // magenta edges
    vec3 bg_col = vec3(0, 0, 0)/256.; // background color is light orange  
    int num_blobs = 20;    
    float thresh = 3000.; // determine size of balls  (larger num = smaller balls)
    
    vec2 uv = fragCoord/iResolution.xy;   
    float aspect = iResolution.y/iResolution.x;
    uv.y *= aspect;      
    
    float dist_sum = 0.;
    // use metaballs for blobs
    for (int  i = 0; i < num_blobs; i++){      
        vec3 blob = get_blob(i,iTime);
        float radius = blob.z;
        vec2 center = blob.xy;       
        center.y *= aspect;
        float dist_to_center = max(length(center - uv)+radius/2.,0.); // add some radius to vary blob size
        float tmp =  (dist_to_center * dist_to_center) ;
        dist_sum += 1. / (tmp*tmp);   
      }
       
    fragColor = vec4(bg_col, 0); 
    if (dist_sum > thresh){
        float t = smoothstep(3.*thresh, 0., dist_sum-(2.*thresh));
        vec3 col = mix(blob_color_center, blob_color_edge, t);
        fragColor = vec4(col, 0);
    }   
       
}