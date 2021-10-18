import { DimlessBinaryDirective } from '~/app/shared/directives/dimless-binary.directive';

export class MockElementRef {
  nativeElement = {};
}

describe('DimlessBinaryDirective', () => {
  it('should create an instance', () => {
    // @ts-ignore
    const directive = new DimlessBinaryDirective(new MockElementRef(), null, null);
    expect(directive).toBeTruthy();
  });
});
