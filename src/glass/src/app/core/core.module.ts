import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TranslateModule } from '@ngx-translate/core';
import { BlockUIModule } from 'ng-block-ui';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { BreadcrumbsComponent } from '~/app/core/navigation-bar/breadcrumbs/breadcrumbs.component';
import { NavigationBarComponent } from '~/app/core/navigation-bar/navigation-bar.component';
import { NavigationBarItemComponent } from '~/app/core/navigation-bar/navigation-bar-item/navigation-bar-item.component';
import { TopBarComponent } from '~/app/core/top-bar/top-bar.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    MainLayoutComponent,
    TopBarComponent,
    NavigationBarComponent,
    InstallerLayoutComponent,
    BlankLayoutComponent,
    NavigationBarItemComponent,
    DeclarativeFormModalComponent,
    BreadcrumbsComponent
  ],
  imports: [
    BlockUIModule.forRoot(),
    CommonModule,
    FlexLayoutModule,
    NgbModule,
    RouterModule,
    DashboardModule,
    TranslateModule.forChild(),
    SharedModule
  ],
  exports: [DashboardModule]
})
export class CoreModule {}
