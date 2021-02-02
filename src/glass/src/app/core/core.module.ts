import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { BlockUIModule } from 'ng-block-ui';

import { MaterialModule } from './../material.modules';
import { MainLayoutComponent } from './layouts/main-layout/main-layout.component';

@NgModule({
  declarations: [MainLayoutComponent],
  imports: [
    BlockUIModule.forRoot(),
    CommonModule,
    MaterialModule,
    RouterModule,
  ],
})
export class CoreModule {}
