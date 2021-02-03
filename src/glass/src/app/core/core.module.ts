import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { BlockUIModule } from 'ng-block-ui';

import { MaterialModule } from './../material.modules';
import { MainLayoutComponent } from './layouts/main-layout/main-layout.component';
import { NavigationBarComponent } from './navigation-bar/navigation-bar.component';
import { TopBarComponent } from './top-bar/top-bar.component';

@NgModule({
  declarations: [MainLayoutComponent, TopBarComponent, NavigationBarComponent],
  imports: [
    BlockUIModule.forRoot(),
    CommonModule,
    MaterialModule,
    RouterModule
  ]
})
export class CoreModule {}
