// Type declaration for leaflet.heat which doesn't have official TypeScript types
declare module 'leaflet.heat' {
  import * as L from 'leaflet';

  interface HeatLatLngTuple extends Array<number> {
    0: number; // latitude
    1: number; // longitude
    2?: number; // intensity (optional)
  }

  interface HeatLayerOptions {
    minOpacity?: number;
    maxZoom?: number;
    max?: number;
    radius?: number;
    blur?: number;
    gradient?: Record<number, string>;
  }

  interface HeatLayer extends L.Layer {
    setLatLngs(latlngs: HeatLatLngTuple[]): this;
    addLatLng(latlng: HeatLatLngTuple): this;
    setOptions(options: HeatLayerOptions): this;
    redraw(): this;
  }

  function heatLayer(
    latlngs: HeatLatLngTuple[],
    options?: HeatLayerOptions
  ): HeatLayer;

  export { heatLayer, HeatLayer, HeatLayerOptions, HeatLatLngTuple };
}

// Extend Leaflet namespace
declare namespace L {
  function heatLayer(
    latlngs: [number, number, number?][],
    options?: {
      minOpacity?: number;
      maxZoom?: number;
      max?: number;
      radius?: number;
      blur?: number;
      gradient?: Record<number, string>;
    }
  ): L.Layer;
}
