import { MapPipe } from '~/app/shared/pipes/map.pipe';

describe('MapPipe', () => {
  const pipe = new MapPipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should transforms [1]', () => {
    expect(pipe.transform(0, { 0: 'Zero' })).toBe('Zero');
  });

  it('should transforms [2]', () => {
    expect(pipe.transform('foo', { bar: 'BAR' })).toBe('foo');
  });
});
