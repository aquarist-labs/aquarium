import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComponentsModule } from '~/app/shared/components/components.module';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';

describe('DeclarativeFormComponent', () => {
  let component: DeclarativeFormComponent;
  let fixture: ComponentFixture<DeclarativeFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComponentsModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DeclarativeFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
