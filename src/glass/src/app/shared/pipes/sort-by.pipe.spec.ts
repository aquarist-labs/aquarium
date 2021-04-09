import { SortByPipe } from '~/app/shared/pipes/sort-by.pipe';

describe('SortByPipe', () => {
  const pipe = new SortByPipe();

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should sort array [1]', () => {
    expect(
      pipe.transform(
        [
          { user: 'fritz', age: 48 },
          { user: 'klaus', age: 36 },
          { user: 'susi', age: 42 },
          { user: 'emma', age: 34 }
        ],
        ['user']
      )
    ).toEqual([
      { user: 'emma', age: 34 },
      { user: 'fritz', age: 48 },
      { user: 'klaus', age: 36 },
      { user: 'susi', age: 42 }
    ]);
  });

  it('should sort array [2]', () => {
    expect(
      pipe.transform(
        [
          { user: 'fritz', age: 48 },
          { user: 'klaus', age: 36 },
          { user: 'susi', age: 42 },
          { user: 'emma', age: 34 }
        ],
        ['age']
      )
    ).toEqual([
      { user: 'emma', age: 34 },
      { user: 'klaus', age: 36 },
      { user: 'susi', age: 42 },
      { user: 'fritz', age: 48 }
    ]);
  });
});
