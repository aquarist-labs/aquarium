import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { MaterialModule } from '~/app/material.modules';

@NgModule({
  imports: [CommonModule, MaterialModule]
})
export class SharedModule {}
