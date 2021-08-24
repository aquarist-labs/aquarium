import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';

import { SanitizePipe } from '~/app/shared/pipes/sanitize.pipe';

describe('SanitizeHtmlPipe', () => {
  let pipe: SanitizePipe;
  let domSanitizer: DomSanitizer;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DomSanitizer]
    });
    domSanitizer = TestBed.inject(DomSanitizer);
    pipe = new SanitizePipe(domSanitizer);
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });
});
