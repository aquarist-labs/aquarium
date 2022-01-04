describe('Dive into Aquarium', () => {
  it('Visit the first tank', () => {
    cy.intercept('GET', '/api/deploy/requirements', { fixture: 'node_qualified.json' });

    cy.visit('/');

    // Welcome page
    cy.contains('Welcome to Aquarium').should('be.visible');
    cy.contains('Check requirements now');
    cy.clickButton('Check requirements now');

    // Requirements check page
    cy.contains('Congratulations! You can now proceed.');
    cy.contains('Next');
    cy.clickButton('Next');

    // Installation device selection
    cy.get('[type="checkbox"]').first().check();
    cy.contains('Install');
    cy.clickButton('Install');

    // Installation mode selection
    cy.contains('Create new cluster').should('be.visible');
    cy.clickButton('Create');

    // Wizard - Start
    cy.contains('This wizard will guide you through the installation process').should('be.visible');
    cy.contains('Start');
    cy.contains('Networking');
    cy.contains('Time');
    cy.contains('Storage');
    cy.contains('Installation');
    cy.contains('Finish');
    cy.contains('Next');
    cy.clickButton('Next');

    // Wizard - Networking
    cy.contains('Hostname').should('be.visible');
    cy.contains('div', 'Hostname').find('input').type('foohost{enter}');
    cy.clickButton('Next');

    // Wizard - Time
    cy.contains('Use an NTP host on the Internet').should('be.visible').click();
    cy.clickButton('Next');

    // Wizard - Storage
    cy.contains('The following devices have been identified for storage in the system').should('be.visible');
    cy.get('[type="checkbox"]').check();
    cy.clickButton('Next');

    // Wizard - Installation
    cy.contains('Aquarium will now install and setup the core system.').should('be.visible');
    cy.clickButton('Install');
  });
});
