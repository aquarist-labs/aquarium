import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';

const routes: Routes = [
  { path: '', redirectTo: '/', pathMatch: 'full' },
  {
    path: '',
    component: MainLayoutComponent,
    children: [],
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
