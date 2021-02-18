import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { MaterialModule } from '~/app/material.modules';

import { SubmitButtonComponent } from './submit-button/submit-button.component';

@NgModule({
  declarations: [SubmitButtonComponent],
  exports: [SubmitButtonComponent],
  imports: [CommonModule, MaterialModule]
})
export class ComponentsModule {}
