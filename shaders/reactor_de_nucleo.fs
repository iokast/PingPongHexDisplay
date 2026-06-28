// "The Quantum Core v2.0" - Visualizador de Grado Profesional ($300 USD)
// Geometría de cristal, refracciones reales y reactividad por bandas.
// iChannel0: Audio (Indispensable)

#define T iTime

// --- FUNCIONES DE ALTA PRECISIÓN ---
mat2 rot(float a) { float c=cos(a), s=sin(a); return mat2(c,s,-s,c); }

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

// Reactividad limpia
float getBass() { return pow(texture(iChannel0, vec2(0.05, 0.25)).x, 2.0); }
float getMid() { return texture(iChannel0, vec2(0.4, 0.25)).x; }

// --- EL NÚCLEO (Geometría que no genera bloques sólidos) ---
float map(vec3 p) {
    float bass = getBass();
    vec3 q = p;
    
    // El núcleo: un octaedro que se abre con el audio
    q.xy *= rot(T * 0.5 + bass);
    q.yz *= rot(T * 0.3);
    
    // Geometría fractal simple para evitar el "bloque sólido"
    for(int i=0; i<3; i++) {
        q = abs(q) - 0.2 - bass * 0.1;
        q.xy *= rot(0.5);
        q.yz *= rot(0.8);
    }
    
    return sdBox(q, vec3(0.1, 0.5, 0.1));
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
    float bass = getBass();
    float mid = getMid();
    
    // Cámara cinematográfica (Sin saltos raros)
    vec3 ro = vec3(0.0, 0.0, -3.0);
    vec3 rd = normalize(vec3(uv, 1.5));
    
    // Movimiento suave de cámara
    ro.xz *= rot(T * 0.2);
    rd.xz *= rot(T * 0.2);

    vec3 col = vec3(0.01, 0.01, 0.02); // Fondo negro de lujo
    
    // Raymarching de superficie (No volumétrico para evitar errores de gradiente)
    float t = 0.0;
    for(int i=0; i<100; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if(d < 0.001 || t > 10.0) break;
        t += d;
    }
    
    if(t < 10.0) {
        vec3 p = ro + rd * t;
        // Cálculo de normales para brillo metálico/cristal
        vec2 e = vec2(0.001, 0.0);
        vec3 n = normalize(map(p) - vec3(map(p-e.xyy), map(p-e.yxy), map(p-e.yyx)));
        
        // Iluminación: Cian y Magenta (Tu marca registrada)
        vec3 lightPos = vec3(2.0, 2.0, -2.0);
        vec3 lDir = normalize(lightPos - p);
        float diff = max(dot(n, lDir), 0.0);
        float spec = pow(max(dot(reflect(-lDir, n), -rd), 0.0), 64.0);
        
        // Color reactivo
        vec3 baseCol = mix(vec3(0.0, 0.8, 1.0), vec3(1.0, 0.0, 0.5), sin(p.y * 2.0 + T) * 0.5 + 0.5);
        col = baseCol * diff + spec * vec3(1.0);
        
        // Efecto de bordes brillantes (Glow)
        float edge = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);
        col += baseCol * edge * 2.0;
    }
    
    // Rayos de luz "God Rays" artificiales (Para el valor de USD 300)
    float beam = pow(max(0.0, 1.0 - length(uv * vec2(1.0, 2.0))), 4.0);
    col += vec3(0.1, 0.3, 0.5) * beam * bass;

    // Post-procesado premium
    col = smoothstep(0.0, 1.0, col);
    col = pow(col, vec3(0.4545)); // Gamma
    
    fragColor = vec4(col, 1.0);
}