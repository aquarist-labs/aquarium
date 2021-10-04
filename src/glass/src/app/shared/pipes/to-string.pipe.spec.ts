import { ToStringPipe } from '~/app/shared/pipes/to-string.pipe';

describe('ToStringPipe', () => {
  const pipe = new ToStringPipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should transform to string [1]', () => {
    expect(pipe.transform(null)).toBe('');
  });

  it('should transform to string [2]', () => {
    expect(pipe.transform(undefined)).toBe('');
  });

  it('should transform to string [3]', () => {
    expect(pipe.transform(1)).toBe('1');
  });
});
