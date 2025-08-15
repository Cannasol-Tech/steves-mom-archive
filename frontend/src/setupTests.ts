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
