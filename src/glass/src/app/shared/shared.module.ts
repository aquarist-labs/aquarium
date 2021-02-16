import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { MaterialModule } from '~/app/material.modules';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { SortByPipe } from '~/app/shared/pipes/sort-by.pipe';

@NgModule({
  declarations: [BytesToSizePipe, SortByPipe],
  exports: [BytesToSizePipe, SortByPipe],
  imports: [CommonModule, MaterialModule]
})
export class SharedModule {}
