require('jest-preset-angular/ngcc-jest-processor');

module.exports = {
  moduleNameMapper: {
    '~/(.*)$': '<rootDir>/src/$1'
  },
  preset: 'jest-preset-angular',
  setupFiles: ['jest-canvas-mock'],
  setupFilesAfterEnv: ['<rootDir>/src/setupJest.ts'],
  testMatch: ['**/*.spec.ts']
};
