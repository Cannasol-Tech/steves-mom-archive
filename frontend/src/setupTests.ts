// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toBeInTheDocument()
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill/mocks for browser APIs not present in jsdom
// matchMedia is used for reduced-motion checks in components like `MessageList`
if (!window.matchMedia) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

// Element.scrollTo is not implemented in jsdom; provide a minimal polyfill
if (!('scrollTo' in Element.prototype)) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (Element.prototype as any).scrollTo = function scrollTo(this: Element, options?: any) {
    // Fallback to directly setting scrollTop when possible
    if (typeof options === 'object' && typeof (options as any).top === 'number') {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      this.scrollTop = (options as any).top;
    }
  };
}

// Lightweight WebSocket mock to avoid jsdom connection errors/noise
// Always override to ensure no real network attempts happen in tests.
// Provides minimal interface used by app code: onopen/onerror/onclose/send/close
class WS {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onopen: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onerror: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onclose: any = null;
  constructor() {
    // open asynchronously to mimic real behavior
    setTimeout(() => this.onopen && this.onopen({} as Event), 0);
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  send(_data: unknown) {}
  close() {
    this.onclose && this.onclose({} as Event);
  }
  addEventListener() {}
  removeEventListener() {}
}
(globalThis as unknown as { WebSocket?: unknown }).WebSocket = WS as unknown as typeof WebSocket;
