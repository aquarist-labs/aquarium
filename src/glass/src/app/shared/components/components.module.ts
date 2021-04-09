import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { TranslateModule } from '@ngx-translate/core';

import { MaterialModule } from '~/app/material.modules';
import { DatatableComponent } from '~/app/shared/components/datatable/datatable.component';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { LanguageButtonComponent } from '~/app/shared/components/language-button/language-button.component';
import { SubmitButtonComponent } from '~/app/shared/components/submit-button/submit-button.component';
import { TokenInputComponent } from '~/app/shared/components/token-input/token-input.component';
import { WidgetComponent } from '~/app/shared/components/widget/widget.component';
import { PipesModule } from '~/app/shared/pipes/pipes.module';

@NgModule({
  declarations: [
    SubmitButtonComponent,
    DialogComponent,
    DatatableComponent,
    LanguageButtonComponent,
    TokenInputComponent,
    WidgetComponent
  ],
  exports: [
    SubmitButtonComponent,
    DialogComponent,
    DatatableComponent,
    LanguageButtonComponent,
    TokenInputComponent,
    WidgetComponent
  ],
  imports: [CommonModule, FlexLayoutModule, MaterialModule, PipesModule, TranslateModule.forChild()]
})
export class ComponentsModule {}
