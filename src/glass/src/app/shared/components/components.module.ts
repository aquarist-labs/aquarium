import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';

import { MaterialModule } from '~/app/material.modules';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { SubmitButtonComponent } from '~/app/shared/components/submit-button/submit-button.component';

@NgModule({
  declarations: [SubmitButtonComponent, DialogComponent],
  exports: [SubmitButtonComponent, DialogComponent],
  imports: [CommonModule, FlexLayoutModule, MaterialModule]
})
export class ComponentsModule {}
