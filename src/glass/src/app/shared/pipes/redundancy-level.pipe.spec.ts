import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';

describe('RedundancyLevelPipe', () => {
  it('create an instance', () => {
    const pipe = new RedundancyLevelPipe();
    expect(pipe).toBeTruthy();
  });
});
