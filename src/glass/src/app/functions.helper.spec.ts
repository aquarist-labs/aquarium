import { toBytes } from '~/app/functions.helper';

describe('functions.helper', () => {
  it('should convert value to bytes [1]', () => {
    expect(toBytes(1024)).toBe(1024);
  });

  it('should convert value to bytes [2]', () => {
    expect(toBytes('1024')).toBe(1024);
  });

  it('should convert value to bytes [3]', () => {
    expect(toBytes('')).toBeNull();
  });

  it('should convert value to bytes [4]', () => {
    expect(toBytes('512B')).toBe(512);
  });

  it('should convert value to bytes [5]', () => {
    expect(toBytes('1 KiB')).toBe(1024);
  });

  it('should convert value to bytes [6]', () => {
    expect(toBytes('1M')).toBe(1048576);
  });
});
