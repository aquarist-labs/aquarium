import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'redundancyLevel'
})
export class RedundancyLevelPipe implements PipeTransform {
  private s: {
    [replicaSize: number]: { longDesc: string; flavor: string; redundancy: string };
  } = {
    1: {
      longDesc:
        // eslint-disable-next-line max-len
        'Only one replica of the data is created, which is reflected in the maximum available storage capacity.',
      flavor: 'Non redundant storage',
      redundancy: 'no'
    },
    2: {
      longDesc:
        // eslint-disable-next-line max-len
        'Two replicas of the data are created. This doubles the required storage capacity. At the same time, the data failure security increases.',
      flavor: 'Redundant storage',
      redundancy: 'one'
    },
    3: {
      longDesc:
        // eslint-disable-next-line max-len
        'Three replicas of the data are created. The required storage capacity triples as a result. The data failure security is even higher.',
      flavor: 'Double redundant storage',
      redundancy: 'two'
    }
  };

  transform(level: number | undefined | null, option: 'flavor' | 'short' | 'long'): string {
    if (!(level && option) || level < 1 || level > 3) {
      return '';
    }
    return option === 'flavor'
      ? this.s[level].flavor
      : option === 'short'
      ? `Can handle ${this.s[level].redundancy} critical hardware failures`
      : this.s[level].longDesc;
  }
}
