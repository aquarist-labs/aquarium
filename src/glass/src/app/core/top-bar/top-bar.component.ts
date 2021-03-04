import { Component, Input, OnInit } from '@angular/core';
import { MatSidenav } from '@angular/material/sidenav';

import { LocalStorageService } from '~/app/shared/services/local-storage.service';

@Component({
  selector: 'glass-top-bar',
  templateUrl: './top-bar.component.html',
  styleUrls: ['./top-bar.component.scss']
})
export class TopBarComponent implements OnInit {
  // eslint-disable-next-line @angular-eslint/no-input-rename
  @Input('navigationSidenav')
  navigationSidenav!: MatSidenav;

  languages = {
    /* eslint-disable @typescript-eslint/naming-convention */
    en_GB: 'English',
    de_DE: 'Deutsch'
  };
  currentLanguage: string;

  constructor(private localStorageService: LocalStorageService) {
    this.currentLanguage = this.localStorageService.get('language', 'en_GB') as string;
  }

  ngOnInit(): void {}

  onToggleNavigationBar() {
    this.navigationSidenav.toggle();
  }

  onSelectLanguage(language: string): void {
    this.localStorageService.set('language', language);
    document.location.replace('');
  }
}
