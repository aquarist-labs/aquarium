import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { MaterialModule } from '~/app/material.modules';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';

@NgModule({
  declarations: [BytesToSizePipe],
  exports: [BytesToSizePipe],
  imports: [CommonModule, MaterialModule]
})
export class SharedModule {}
