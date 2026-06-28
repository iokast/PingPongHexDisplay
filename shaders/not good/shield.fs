vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void mainImage(out vec4 O, vec2 I) {
    // Rotate the output by 90 degrees counterclockwise
    I = vec2(iResolution.y - I.y, I.x);

    float zoom = .75 + 0.2 * sin(iTime * 0.5);

    // Iterator, z, and time
    float i, z, t = iTime;

    // Clear frag and loop 100 times
    for (O *= i; i < 1.; i += .01) {
        // Resolution for scaling
        vec2 v = iResolution.xy,
        // Center and scale outward
        p = (I + I - v) / v.y * i;

        p/=zoom;

        // Sphere distortion and compute z
        p /= .2 + sqrt(z = max(1. - dot(p, p), 0.)) * .3;

        // Offset for hex pattern
        p.y += fract(ceil(p.x = p.x / .9 + t) * .5) + t * .2;

        // Mirror quadrants
        v = abs(fract(p) - .5);

        // Add color and fade outward
        // Convert HSV to RGB and add color
        // vec3 color = hsv2rgb(vec3(mod(t * 0.1, 1.0), 1.0, 1.0));
        // O += vec4(color, 1) / 2e3 * z /
        O += vec4(2, 3, 5, 1) / 2e3 * z /
            // Compute hex distance
            (abs(max(v.x * 1.5 + v, v + v).y - 1.) + .1 - i * .09);
    }

    // Tanh tonemap
    O = 1.0 / (1.0 + exp(-O * 3.0 + 3.0));
}
