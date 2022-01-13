import '@angular/localize/init';
import 'jest-preset-angular/setup-jest';

Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => ''
  })
});

(async () => {
  if ('ResizeObserver' in window === false) {
    // Loads polyfill asynchronously, only if required.
    const module = await import('@juggle/resize-observer');
    window.ResizeObserver = module.ResizeObserver;
  }
})();
