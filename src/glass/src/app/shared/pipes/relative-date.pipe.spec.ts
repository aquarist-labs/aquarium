import dayjs from 'dayjs';

import { RelativeDatePipe } from '~/app/shared/pipes/relative-date.pipe';

describe('RelativeDatePipe', () => {
  const pipe = new RelativeDatePipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should transform [1]', () => {
    expect(pipe.transform(-25)).toBe('a few seconds ago');
  });

  it('should transform [2]', () => {
    expect(pipe.transform(-80, true)).toBe('a minute');
  });

  it('should transform [3]', () => {
    const date = dayjs().subtract(1, 'hour');
    expect(pipe.transform(date.toDate())).toBe('an hour ago');
  });

  it('should transform [4]', () => {
    const date = dayjs().subtract(2, 'days');
    expect(pipe.transform(date.toDate(), true)).toBe('2 days');
  });

  it('should transform [5]', () => {
    const date = dayjs().subtract(1, 'month');
    expect(pipe.transform(date.unix())).toBe('a month ago');
  });
});
