import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { AutofocusDirective } from '~/app/shared/directives/autofocus.directive';
import { DimlessBinaryDirective } from '~/app/shared/directives/dimless-binary.directive';

@NgModule({
  declarations: [AutofocusDirective, DimlessBinaryDirective],
  exports: [AutofocusDirective, DimlessBinaryDirective],
  imports: [CommonModule]
})
export class DirectivesModule {}
