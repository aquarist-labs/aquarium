import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { ArrayPipe } from '~/app/shared/pipes/array.pipe';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { MapPipe } from '~/app/shared/pipes/map.pipe';
import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';
import { RelativeDatePipe } from '~/app/shared/pipes/relative-date.pipe';
import { SanitizePipe } from '~/app/shared/pipes/sanitize.pipe';
import { SortByPipe } from '~/app/shared/pipes/sort-by.pipe';
import { ToStringPipe } from '~/app/shared/pipes/to-string.pipe';

@NgModule({
  declarations: [
    ArrayPipe,
    BytesToSizePipe,
    SanitizePipe,
    SortByPipe,
    RelativeDatePipe,
    RedundancyLevelPipe,
    MapPipe,
    ToStringPipe
  ],
  providers: [
    ArrayPipe,
    BytesToSizePipe,
    SanitizePipe,
    SortByPipe,
    RelativeDatePipe,
    RedundancyLevelPipe,
    MapPipe,
    ToStringPipe
  ],
  exports: [
    ArrayPipe,
    BytesToSizePipe,
    SanitizePipe,
    SortByPipe,
    RelativeDatePipe,
    RedundancyLevelPipe,
    MapPipe,
    ToStringPipe
  ],
  imports: [CommonModule]
})
export class PipesModule {}
