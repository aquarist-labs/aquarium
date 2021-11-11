import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TranslateModule } from '@ngx-translate/core';

import { AlertPanelComponent } from '~/app/shared/components/alert-panel/alert-panel.component';
import { ContentPageComponent } from '~/app/shared/components/content-page/content-page.component';
import { DatatableComponent } from '~/app/shared/components/datatable/datatable.component';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { LanguageButtonComponent } from '~/app/shared/components/language-button/language-button.component';
import { SubmitButtonComponent } from '~/app/shared/components/submit-button/submit-button.component';
import { WidgetComponent } from '~/app/shared/components/widget/widget.component';
import { DirectivesModule } from '~/app/shared/directives/directives.module';
import { PipesModule } from '~/app/shared/pipes/pipes.module';

@NgModule({
  declarations: [
    SubmitButtonComponent,
    DialogComponent,
    DatatableComponent,
    LanguageButtonComponent,
    WidgetComponent,
    DeclarativeFormComponent,
    AlertPanelComponent,
    ContentPageComponent
  ],
  exports: [
    SubmitButtonComponent,
    DialogComponent,
    DatatableComponent,
    LanguageButtonComponent,
    WidgetComponent,
    DeclarativeFormComponent,
    AlertPanelComponent,
    ContentPageComponent
  ],
  imports: [
    CommonModule,
    DirectivesModule,
    FlexLayoutModule,
    FormsModule,
    NgbModule,
    PipesModule,
    ReactiveFormsModule,
    TranslateModule.forChild()
  ]
})
export class ComponentsModule {}
