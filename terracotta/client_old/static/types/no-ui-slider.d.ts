/**
 * Not the real type definitions, but just enough for this client.
 * @see https://pics.me.me/duck-typing-duck-typing-2429782.png - an accurate representation of this module.
 */
export as namespace noUiSlider;

export function updateOptions(...any): any;
export function create(...any): any;
export function on(...any): any;
export function get(...any): any;
export function set(...any): any;

export interface SliderElement extends HTMLElement {
  noUiSlider: {
    updateOptions;
    create;
    on;
    get;
    set;
  }
}
