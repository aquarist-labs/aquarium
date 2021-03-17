import { Component, Input } from '@angular/core';
import { MatSidenav } from '@angular/material/sidenav';

@Component({
  selector: 'glass-top-bar',
  templateUrl: './top-bar.component.html',
  styleUrls: ['./top-bar.component.scss']
})
export class TopBarComponent {
  // eslint-disable-next-line @angular-eslint/no-input-rename
  @Input('navigationSidenav')
  navigationSidenav!: MatSidenav;

  constructor() {}

  onToggleNavigationBar() {
    this.navigationSidenav.toggle();
  }
}
