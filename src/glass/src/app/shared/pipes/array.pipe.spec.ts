import { ArrayPipe } from '~/app/shared/pipes/array.pipe';

describe('ArrayPipe', () => {
  const pipe = new ArrayPipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('transforms string to array', () => {
    expect(pipe.transform('foo')).toEqual(['foo']);
  });

  it('transforms array to array', () => {
    expect(pipe.transform(['foo'], true)).toEqual([['foo']]);
  });

  it('do not transforms array to array', () => {
    expect(pipe.transform(['foo'])).toEqual(['foo']);
  });
});
