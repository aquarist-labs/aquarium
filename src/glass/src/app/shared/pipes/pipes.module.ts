import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { MapPipe } from '~/app/shared/pipes/map.pipe';
import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';
import { RelativeDatePipe } from '~/app/shared/pipes/relative-date.pipe';
import { SortByPipe } from '~/app/shared/pipes/sort-by.pipe';

@NgModule({
  declarations: [BytesToSizePipe, SortByPipe, RelativeDatePipe, RedundancyLevelPipe, MapPipe],
  providers: [BytesToSizePipe, SortByPipe, RelativeDatePipe, RedundancyLevelPipe, MapPipe],
  exports: [BytesToSizePipe, SortByPipe, RelativeDatePipe, RedundancyLevelPipe, MapPipe],
  imports: [CommonModule]
})
export class PipesModule {}
