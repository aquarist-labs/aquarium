import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { BlockUIModule } from 'ng-block-ui';

import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { NavigationBarComponent } from '~/app/core/navigation-bar/navigation-bar.component';
import { TopBarComponent } from '~/app/core/top-bar/top-bar.component';
import { MaterialModule } from '~/app/material.modules';

@NgModule({
  declarations: [
    MainLayoutComponent,
    TopBarComponent,
    NavigationBarComponent,
    InstallerLayoutComponent,
    BlankLayoutComponent
  ],
  imports: [BlockUIModule.forRoot(), CommonModule, MaterialModule, RouterModule]
})
export class CoreModule {}
