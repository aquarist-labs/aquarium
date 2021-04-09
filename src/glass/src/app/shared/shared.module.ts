import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { MaterialModule } from '~/app/material.modules';
import { ComponentsModule } from '~/app/shared/components/components.module';
import { PipesModule } from '~/app/shared/pipes/pipes.module';

@NgModule({
  exports: [ComponentsModule, PipesModule],
  imports: [CommonModule, ComponentsModule, MaterialModule, PipesModule]
})
export class SharedModule {}
