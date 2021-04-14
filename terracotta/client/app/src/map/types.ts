export interface Viewport {
    longitude: number,
    latitude: number,
    zoom?: number,
    bearing?: number,
    pitch?: number,
    transitionDuration?: number,
    transitionInterpolator?: any,
    transitionEasing?: Function
}