import '@angular/localize/init';
import 'jest-preset-angular/setup-jest';

Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => ''
  })
});
