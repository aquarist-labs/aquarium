import { Component, Input } from '@angular/core';
import { MatSidenav } from '@angular/material/sidenav';

import { getCurrentLanguage, setCurrentLanguage, supportedLanguages } from '~/app/i18n.helper';

@Component({
  selector: 'glass-top-bar',
  templateUrl: './top-bar.component.html',
  styleUrls: ['./top-bar.component.scss']
})
export class TopBarComponent {
  // eslint-disable-next-line @angular-eslint/no-input-rename
  @Input('navigationSidenav')
  navigationSidenav!: MatSidenav;

  languages = supportedLanguages;
  currentLanguage: string;

  constructor() {
    this.currentLanguage = getCurrentLanguage();
  }

  onToggleNavigationBar() {
    this.navigationSidenav.toggle();
  }

  onSelectLanguage(language: string): void {
    setCurrentLanguage(language);
    document.location.replace('');
  }
}
