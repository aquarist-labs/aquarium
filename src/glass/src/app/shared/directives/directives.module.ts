import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { AutofocusDirective } from '~/app/shared/directives/autofocus.directive';

@NgModule({
  declarations: [AutofocusDirective],
  exports: [AutofocusDirective],
  imports: [CommonModule]
})
export class DirectivesModule {}
