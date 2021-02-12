import { BytesToSizePipe } from './bytes-to-size.pipe';

describe('BytesToSizePipe', () => {
  const pipe = new BytesToSizePipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('transforms 0 bytes', () => {
    expect(pipe.transform(0)).toBe('0 Bytes');
  });

  it('transforms 1024^0', () => {
    const value = Math.pow(1024, 0);
    expect(pipe.transform(value)).toBe('1 Bytes');
  });

  it('transforms 1024^1', () => {
    const value = Math.pow(1024, 1);
    expect(pipe.transform(value)).toBe('1 KB');
  });

  it('transforms 1024^2', () => {
    const value = Math.pow(1024, 2);
    expect(pipe.transform(value)).toBe('1 MB');
  });

  it('transforms 1024^3', () => {
    const value = Math.pow(1024, 3);
    expect(pipe.transform(value)).toBe('1 GB');
  });

  it('transforms 1024^4', () => {
    const value = Math.pow(1024, 4);
    expect(pipe.transform(value)).toBe('1 TB');
  });

  it('transforms 1024^5', () => {
    const value = Math.pow(1024, 5);
    expect(pipe.transform(value)).toBe('1 PB');
  });

  it('transforms 1024^6', () => {
    const value = Math.pow(1024, 6);
    expect(pipe.transform(value)).toBe('1 EB');
  });

  it('transforms 1024^7', () => {
    const value = Math.pow(1024, 7);
    expect(pipe.transform(value)).toBe('1 ZB');
  });

  it('transforms 1024^8', () => {
    const value = Math.pow(1024, 8);
    expect(pipe.transform(value)).toBe('1 YB');
  });
});
