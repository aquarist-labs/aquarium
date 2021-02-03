import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { BlockUIModule } from 'ng-block-ui';

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
    InstallerLayoutComponent
  ],
  imports: [BlockUIModule.forRoot(), CommonModule, MaterialModule, RouterModule]
})
export class CoreModule {}
