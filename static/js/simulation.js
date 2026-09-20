/**
 * KINETIC POUR OS // 3D DIGITAL TWIN & FLUIDICS SIMULATION ENGINE
 * 8-Bottle Automated Drink-Dispensing Table with Physical Fluid Animation
 * Features:
 *  - 8 Bordeaux-style bottles in a 2x4 in-house 3D printed modular crate
 *  - REAL DRAIN ANIMATION: Liquid level visibly drops inside active bottles
 *  - VISIBLE TUBE FLOW: Fluid droplets / pulses travel through transparent silicone lines
 *  - 8x GROTHEN 24V peristaltic dosing pump heads with rotating 3-roller assemblies
 *  - 8-port custom 3D-printed central nozzle manifold with fluid streams
 *  - Stepper-driven T8 lead screw elevator lowering and raising the cup
 *  - Live synchronization with PLC State Machine algorithm cards on page
 */

(function () {
  'use strict';

  let scene, camera, renderer, controls;
  let tableGroup, elevatorGroup, cupMesh, cupLiquidMesh, liquidStreamMesh;
  let bottles = []; // Array of 8 bottle objects { group, liquidMesh, initialHeight, currentLevel, color, name }
  let pumpRollers = []; // 8 pump rotor groups
  let tubeCurves = []; // 8 3D curves
  let fluidPulses = []; // Array of moving fluid droplet meshes traveling along tubes
  let isXRay = true;
  let cutawayPanels = [];

  let desiredCameraPos = new THREE.Vector3(0, 170, 240);
  let desiredCameraTarget = new THREE.Vector3(0, 45, 0);

  // Dispensing State Machine Constants
  const STATE_IDLE = 0;
  const STATE_LOWERING = 1;
  const STATE_DISPENSING = 2;
  const STATE_PURGING = 3;
  const STATE_RISING = 4;
  const STATE_COMPLETE = 5;
  let cycleState = STATE_IDLE;
  let cycleProgress = 0;

  let cupPresent = false;
  let cupElevatorY = 95;
  const ELEVATOR_TOP_Y = 95;
  const ELEVATOR_BOTTOM_Y = 25;

  // 8 Bottle Configurations (2x4 array)
  const BOTTLE_CONFIGS = [
    { id: 0, name: "Bourbon", color: 0x963600, row: 0, col: 0 },
    { id: 1, name: "Vodka", color: 0xdde5ed, row: 0, col: 1 },
    { id: 2, name: "Gin", color: 0x8a2be2, row: 0, col: 2 },
    { id: 3, name: "Tequila", color: 0xe68a00, row: 0, col: 3 },
    { id: 4, name: "Triple Sec", color: 0xffaa00, row: 1, col: 0 },
    { id: 5, name: "Cranberry", color: 0xd61a3c, row: 1, col: 1 },
    { id: 6, name: "Tonic", color: 0x00f0ff, row: 1, col: 2 },
    { id: 7, name: "Citrus Sour", color: 0xffe600, row: 1, col: 3 }
  ];

  // Active Drink Recipe
  let currentRecipe = {
    name: "Old Fashioned",
    activeBottles: [0, 7], // Bourbon + Citrus
    blendColor: 0xa84200,
    duration: 4.0
  };

  // Subsystem Camera Preset Positions
  const CAMERA_VIEWS = {
    all: { pos: new THREE.Vector3(0, 170, 240), target: new THREE.Vector3(0, 45, 0), name: "FULL SYSTEM // TABLE CUTAWAY" },
    bottling: { pos: new THREE.Vector3(-65, 95, 115), target: new THREE.Vector3(-45, 35, 0), name: "BOTTLING BAY // 8-BOTTLE 3D CRATE" },
    manifold: { pos: new THREE.Vector3(0, 130, 80), target: new THREE.Vector3(0, 78, 0), name: "FLUIDICS // 8-PORT MANIFOLD & PUMPS" },
    lift: { pos: new THREE.Vector3(45, 90, 85), target: new THREE.Vector3(0, 50, 0), name: "MECHANICAL // LEAD SCREW ELEVATOR" },
    plc: { pos: new THREE.Vector3(75, 60, 80), target: new THREE.Vector3(50, 25, -20), name: "ELECTRICAL // PLC & SENSORS" }
  };

  // Material Library (Optimized for High-Performance 60 FPS across Mobile & Desktop)
  const matObsidian = new THREE.MeshStandardMaterial({ color: 0x101015, metalness: 0.85, roughness: 0.25 });
  const matBrushedMetal = new THREE.MeshStandardMaterial({ color: 0x909099, metalness: 0.95, roughness: 0.25 });
  const matSmokedAcrylic = new THREE.MeshStandardMaterial({
    color: 0x121218,
    metalness: 0.25,
    roughness: 0.15,
    transparent: true,
    opacity: 0.45
  });
  const matPrintedPLA = new THREE.MeshStandardMaterial({ color: 0x22222a, roughness: 0.75, metalness: 0.15 });
  const matGlass = new THREE.MeshStandardMaterial({
    color: 0xecf4ff,
    metalness: 0.1,
    roughness: 0.05,
    transparent: true,
    opacity: 0.65
  });
  const matSiliconeTube = new THREE.MeshStandardMaterial({
    color: 0xecfeff,
    roughness: 0.25,
    transparent: true,
    opacity: 0.55
  });

  function init() {
    const container = document.getElementById('three-viewport');
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 680;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060608);
    scene.fog = new THREE.FogExp2(0x060608, 0.0022);

    camera = new THREE.PerspectiveCamera(40, width / height, 1, 1500);
    camera.position.copy(CAMERA_VIEWS.all.pos);

    renderer = new THREE.WebGLRenderer({
      canvas: document.getElementById('three-canvas'),
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    if (window.THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.maxPolarAngle = Math.PI / 2 - 0.02;
      controls.minDistance = 35;
      controls.maxDistance = 550;
      controls.target.copy(CAMERA_VIEWS.all.target);
    }

    setupLighting();
    buildTableStructure();
    build8BottleCrate();
    buildManifoldAndPumps();
    buildElevatorMechanism();
    buildElectricalAndPLC();
    buildGroundGrid();

    window.addEventListener('resize', onWindowResize);

    logTerminal("SYS_INIT", "3D Digital Twin Simulation initialized with 8-bottle fluid dynamics.", "ok");
    updatePlcStep(1); // Ready at step 1

    animate();
  }

  function setupLighting() {
    scene.add(new THREE.AmbientLight(0x383048, 2.2));

    const keySpot = new THREE.SpotLight(0xff3b14, 4.2, 380, Math.PI / 3.8, 0.45, 1.2);
    keySpot.position.set(70, 180, 110);
    keySpot.castShadow = true;
    keySpot.shadow.bias = -0.0008;
    keySpot.shadow.mapSize.width = 1024;
    keySpot.shadow.mapSize.height = 1024;
    scene.add(keySpot);

    const uvPoint = new THREE.PointLight(0x8b24e3, 2.8, 280);
    uvPoint.position.set(-85, 130, -70);
    scene.add(uvPoint);

    // Warm chamber light
    const chamberLight = new THREE.PointLight(0xff5722, 2.8, 160);
    chamberLight.position.set(0, 95, 0);
    scene.add(chamberLight);

    // Studio fill lights for crisp mechanical & tabletop definition
    const topLight = new THREE.DirectionalLight(0xffffff, 1.3);
    topLight.position.set(30, 220, 100);
    scene.add(topLight);

    const cyanRim = new THREE.DirectionalLight(0x00f0ff, 0.8);
    cyanRim.position.set(-80, 140, 100);
    scene.add(cyanRim);
  }

  function buildTableStructure() {
    tableGroup = new THREE.Group();
    scene.add(tableGroup);

    // Top surface with center aperture
    const topShape = new THREE.Shape();
    topShape.moveTo(-100, -65);
    topShape.lineTo(100, -65);
    topShape.lineTo(100, 65);
    topShape.lineTo(-100, 65);
    topShape.lineTo(-100, -65);

    const holePath = new THREE.Path();
    holePath.absarc(0, 0, 18, 0, Math.PI * 2, true);
    topShape.holes.push(holePath);

    const topGeom = new THREE.ExtrudeGeometry(topShape, { depth: 5, bevelEnabled: true, bevelSegments: 3, steps: 1, bevelSize: 1 });
    topGeom.rotateX(Math.PI / 2);

    const tableTopMesh = new THREE.Mesh(topGeom, matObsidian);
    tableTopMesh.position.set(0, 100, 0);
    tableTopMesh.receiveShadow = true;
    tableTopMesh.castShadow = true;
    tableGroup.add(tableTopMesh);

    // Aperture Infrared Rim
    const rimGeom = new THREE.RingGeometry(18, 20.5, 48);
    rimGeom.rotateX(-Math.PI / 2);
    const rimMesh = new THREE.Mesh(rimGeom, new THREE.MeshBasicMaterial({ color: 0xff3b14, side: THREE.DoubleSide }));
    rimMesh.position.set(0, 100.1, 0);
    tableGroup.add(rimMesh);



    // 4 Corner Legs
    const legGeom = new THREE.CylinderGeometry(3.5, 3.5, 96, 16);
    const legPositions = [[-92, 48, -57], [92, 48, -57], [-92, 48, 57], [92, 48, 57]];
    legPositions.forEach(pos => {
      const leg = new THREE.Mesh(legGeom, matBrushedMetal);
      leg.position.set(pos[0], pos[1], pos[2]);
      leg.castShadow = true;
      tableGroup.add(leg);

      const pad = new THREE.Mesh(new THREE.CylinderGeometry(5, 5.5, 4, 16), matObsidian);
      pad.position.set(pos[0], 2, pos[2]);
      tableGroup.add(pad);
    });

    // Lower Utility Shelf
    const shelfGeom = new THREE.BoxGeometry(185, 4, 115);
    const shelf = new THREE.Mesh(shelfGeom, matObsidian);
    shelf.position.set(0, 8, 0);
    shelf.receiveShadow = true;
    tableGroup.add(shelf);

    // Smoked Acrylic Cutaway Panels
    const frontPanel = new THREE.Mesh(new THREE.BoxGeometry(180, 82, 2), matSmokedAcrylic);
    frontPanel.position.set(0, 52, 59);
    cutawayPanels.push(frontPanel);
    tableGroup.add(frontPanel);

    const leftPanel = new THREE.Mesh(new THREE.BoxGeometry(2, 82, 110), matSmokedAcrylic);
    leftPanel.position.set(-93, 52, 0);
    cutawayPanels.push(leftPanel);
    tableGroup.add(leftPanel);

    const rightPanel = new THREE.Mesh(new THREE.BoxGeometry(2, 82, 110), matSmokedAcrylic);
    rightPanel.position.set(93, 52, 0);
    cutawayPanels.push(rightPanel);
    tableGroup.add(rightPanel);
  }

  function build8BottleCrate() {
    const bottlingGroup = new THREE.Group();
    bottlingGroup.position.set(-50, 10, 0);
    tableGroup.add(bottlingGroup);

    // In-House 3D Printed 8-Slot Reservoir Crate (2 rows x 4 cols)
    const crateWidth = 65;
    const crateDepth = 80;
    const crateBase = new THREE.Mesh(new THREE.BoxGeometry(crateWidth, 6, crateDepth), matPrintedPLA);
    crateBase.position.set(0, 3, 0);
    crateBase.castShadow = true;
    bottlingGroup.add(crateBase);

    // Crate Dividers & Honeycomb Ribs
    for (let col = -1.5; col <= 1.5; col += 1) {
      const divider = new THREE.Mesh(new THREE.BoxGeometry(2, 20, crateDepth - 6), matPrintedPLA);
      divider.position.set(col * 14.5, 12, 0);
      bottlingGroup.add(divider);
    }
    const centerDivider = new THREE.Mesh(new THREE.BoxGeometry(crateWidth - 6, 20, 2), matPrintedPLA);
    centerDivider.position.set(0, 12, 0);
    bottlingGroup.add(centerDivider);

    // Instantiate 8 Bordeaux-Style Bottles
    bottles = [];
    tubeCurves = [];

    BOTTLE_CONFIGS.forEach((cfg) => {
      const bottleGroup = new THREE.Group();
      // Position inside crate: 2 rows (z: -18, +18), 4 columns (x: -21, -7, +7, +21)
      const posX = -21 + cfg.col * 14;
      const posZ = -18 + cfg.row * 36;
      bottleGroup.position.set(posX, 6, posZ);
      bottlingGroup.add(bottleGroup);

      // Glass Bottle Body (750ml Bordeaux shape)
      const bodyGeom = new THREE.CylinderGeometry(4.6, 4.6, 24, 20);
      const bottleGlass = new THREE.Mesh(bodyGeom, matGlass);
      bottleGlass.position.y = 12;
      bottleGlass.castShadow = true;
      bottleGroup.add(bottleGlass);

      // Liquid Cylinder Mesh (will visually drop as dispensed!)
      const initialLiquidHeight = 18;
      const liquidGeom = new THREE.CylinderGeometry(4.3, 4.3, initialLiquidHeight, 20);
      const liquidMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        roughness: 0.15,
        metalness: 0.1,
        transparent: true,
        opacity: 0.85,
        emissive: cfg.color,
        emissiveIntensity: 0.15
      });
      const liquidMesh = new THREE.Mesh(liquidGeom, liquidMat);
      liquidMesh.position.y = initialLiquidHeight / 2 + 0.5;
      bottleGroup.add(liquidMesh);

      // Shoulder Cone
      const shoulderGeom = new THREE.CylinderGeometry(1.8, 4.6, 5, 20);
      const shoulder = new THREE.Mesh(shoulderGeom, matGlass);
      shoulder.position.y = 26.5;
      bottleGroup.add(shoulder);

      // Neck & Capsule Foil
      const neckGeom = new THREE.CylinderGeometry(1.4, 1.4, 7, 16);
      const neck = new THREE.Mesh(neckGeom, matGlass);
      neck.position.y = 32.5;
      bottleGroup.add(neck);

      const capsuleMat = new THREE.MeshStandardMaterial({ color: 0xff3b14, metalness: 0.3, roughness: 0.4 });
      const capsule = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 4, 16), capsuleMat);
      capsule.position.y = 35;
      bottleGroup.add(capsule);

      // Inline One-Way Check Valve on bottle neck
      const valveMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 4, 12), matGlass);
      valveMesh.position.y = 40;
      bottleGroup.add(valveMesh);

      // Store bottle reference for dynamic fluid drain animation
      bottles.push({
        id: cfg.id,
        name: cfg.name,
        group: bottleGroup,
        liquidMesh: liquidMesh,
        initialHeight: initialLiquidHeight,
        currentFill: 1.0, // 100% full initially
        color: cfg.color,
        worldTopPos: new THREE.Vector3(posX - 50, 48, posZ)
      });

      // Silicone Tubing from this bottle's check valve to the manifold
      const manifoldTarget = new THREE.Vector3(-4 + (cfg.col) * 2.5, 78, -3 + (cfg.row) * 6);
      const midControl = new THREE.Vector3((posX - 50) * 0.45, 74, posZ * 0.5);
      const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(posX - 50, 48, posZ),
        midControl,
        manifoldTarget
      );
      tubeCurves.push(curve);

      const tubeGeom = new THREE.TubeGeometry(curve, 24, 0.65, 8, false);
      const tubeMesh = new THREE.Mesh(tubeGeom, matSiliconeTube);
      tableGroup.add(tubeMesh);
    });

    // Create moving fluid droplet beads for all 8 tubes
    createFluidPulses();
  }

  function createFluidPulses() {
    fluidPulses = [];
    tubeCurves.forEach((curve, idx) => {
      const pulseGroup = new THREE.Group();
      tableGroup.add(pulseGroup);

      // 4 droplet beads per tube that advance when pump is active
      const beads = [];
      for (let b = 0; b < 4; b++) {
        const beadGeom = new THREE.SphereGeometry(0.85, 12, 12);
        const beadMat = new THREE.MeshStandardMaterial({
          color: BOTTLE_CONFIGS[idx].color,
          emissive: BOTTLE_CONFIGS[idx].color,
          emissiveIntensity: 0.9,
          transparent: true,
          opacity: 0.95
        });
        const bead = new THREE.Mesh(beadGeom, beadMat);
        bead.visible = false;
        pulseGroup.add(bead);
        beads.push({ mesh: bead, offset: b * 0.25 });
      }

      fluidPulses.push({ tubeIndex: idx, beads: beads, active: false });
    });
  }

  function buildManifoldAndPumps() {
    const pumpBay = new THREE.Group();
    pumpBay.position.set(0, 78, 0);
    tableGroup.add(pumpBay);

    // Central 3D-Printed Manifold (8-Port Inlets)
    const manifoldMesh = new THREE.Mesh(new THREE.CylinderGeometry(11, 9, 8, 12), matPrintedPLA);
    manifoldMesh.castShadow = true;
    pumpBay.add(manifoldMesh);

    // 8 Nozzle tips extending down into cup chamber
    for (let i = 0; i < 8; i++) {
      const angle = (i * Math.PI * 2) / 8;
      const nx = Math.cos(angle) * 4.5;
      const nz = Math.sin(angle) * 4.5;
      const nozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.35, 4.5, 10), matBrushedMetal);
      nozzle.position.set(nx, -5.5, nz);
      pumpBay.add(nozzle);
    }

    // 8x GROTHEN 24V Dosing Peristaltic Pumps around the perimeter
    pumpRollers = [];
    for (let p = 0; p < 8; p++) {
      const angle = (p * Math.PI * 2) / 8;
      const radius = 24;
      const px = Math.cos(angle) * radius;
      const pz = Math.sin(angle) * radius;

      const pGroup = new THREE.Group();
      pGroup.position.set(px, 0, pz);
      pGroup.rotation.y = -angle + Math.PI / 2;
      pumpBay.add(pGroup);

      // Motor Back Cylinder
      const motor = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 3.5, 8, 16), matBrushedMetal);
      motor.rotation.x = Math.PI / 2;
      motor.position.z = -5.5;
      pGroup.add(motor);

      // Flat-Panel Head
      const head = new THREE.Mesh(new THREE.BoxGeometry(7.5, 7.5, 3.5), matPrintedPLA);
      pGroup.add(head);

      // Transparent Cover
      const cover = new THREE.Mesh(new THREE.CylinderGeometry(3.0, 3.0, 1.0, 16), matGlass);
      cover.rotation.x = Math.PI / 2;
      cover.position.z = 2.0;
      pGroup.add(cover);

      // 3-Roller Rotor that spins!
      const rotor = new THREE.Group();
      rotor.position.z = 1.9;
      pGroup.add(rotor);
      pumpRollers.push(rotor);

      for (let r = 0; r < 3; r++) {
        const ra = (r * Math.PI * 2) / 3;
        const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.8, 10), matBrushedMetal);
        roller.rotation.x = Math.PI / 2;
        roller.position.set(Math.cos(ra) * 1.8, Math.sin(ra) * 1.8, 0);
        rotor.add(roller);
      }
    }

    // Dynamic Liquid Stream Mesh (fires down from manifold into cup)
    const streamGeom = new THREE.CylinderGeometry(0.8, 1.6, 45, 16);
    const streamMat = new THREE.MeshStandardMaterial({
      color: 0xff3b14,
      emissive: 0xff3b14,
      emissiveIntensity: 0.8,
      transparent: true,
      opacity: 0.9
    });
    liquidStreamMesh = new THREE.Mesh(streamGeom, streamMat);
    liquidStreamMesh.position.set(0, -28, 0);
    liquidStreamMesh.visible = false;
    pumpBay.add(liquidStreamMesh);
  }

  function buildElevatorMechanism() {
    elevatorGroup = new THREE.Group();
    tableGroup.add(elevatorGroup);

    // NEMA 17 Stepper & T8 Lead Screw
    const stepper = new THREE.Mesh(new THREE.BoxGeometry(8, 8, 8), matObsidian);
    stepper.position.set(0, 12, 0);
    tableGroup.add(stepper);

    const leadScrew = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 85, 16), matBrushedMetal);
    leadScrew.position.set(0, 56, 0);
    tableGroup.add(leadScrew);

    // Guide Rods
    const rodL = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 85, 16), matBrushedMetal);
    rodL.position.set(-11, 56, 0);
    tableGroup.add(rodL);

    const rodR = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 85, 16), matBrushedMetal);
    rodR.position.set(11, 56, 0);
    tableGroup.add(rodR);

    // Elevator Carriage Platform
    const carriage = new THREE.Mesh(new THREE.CylinderGeometry(16, 17, 3, 32), matObsidian);
    carriage.castShadow = true;
    carriage.receiveShadow = true;
    elevatorGroup.add(carriage);

    const coaster = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 0.5, 32), new THREE.MeshStandardMaterial({ color: 0x1a1a24 }));
    coaster.position.y = 1.6;
    elevatorGroup.add(coaster);

    // Glass Cup & Internal Liquid
    const cupGroup = new THREE.Group();
    cupGroup.position.y = 1.8;
    elevatorGroup.add(cupGroup);

    cupMesh = new THREE.Mesh(new THREE.CylinderGeometry(6.2, 5.0, 15, 24, 1, true), matGlass);
    cupMesh.position.y = 7.5;
    cupMesh.castShadow = true;
    cupGroup.add(cupMesh);

    const cupBase = new THREE.Mesh(new THREE.CylinderGeometry(5.0, 5.0, 1.0, 24), matGlass);
    cupBase.position.y = 0.5;
    cupGroup.add(cupBase);

    // Liquid in Cup
    cupLiquidMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(5.8, 4.8, 12, 24),
      new THREE.MeshStandardMaterial({
        color: currentRecipe.blendColor,
        roughness: 0.1,
        metalness: 0.1,
        transparent: true,
        opacity: 0.9,
        emissive: currentRecipe.blendColor,
        emissiveIntensity: 0.25
      })
    );
    cupLiquidMesh.position.y = 6.5;
    cupLiquidMesh.scale.set(1, 0.001, 1);
    cupGroup.add(cupLiquidMesh);

    cupGroup.visible = false;
    elevatorGroup.userData.cupGroup = cupGroup;

    elevatorGroup.position.set(0, ELEVATOR_TOP_Y, 0);
  }

  function buildElectricalAndPLC() {
    const elecGroup = new THREE.Group();
    elecGroup.position.set(55, 12, 0);
    tableGroup.add(elecGroup);

    // DIN Rail Backing & PLC Unit
    const plate = new THREE.Mesh(new THREE.BoxGeometry(45, 36, 2), matObsidian);
    plate.position.set(0, 22, -28);
    elecGroup.add(plate);

    const pcb = new THREE.Mesh(new THREE.BoxGeometry(22, 18, 1.2), new THREE.MeshStandardMaterial({ color: 0x0f2d18 }));
    pcb.position.set(-8, 22, -26.5);
    elecGroup.add(pcb);

    // 8-Channel Relay Module
    const relayPcb = new THREE.Mesh(new THREE.BoxGeometry(16, 28, 1.2), matObsidian);
    relayPcb.position.set(12, 22, -26.5);
    elecGroup.add(relayPcb);

    for (let r = 0; r < 8; r++) {
      const relay = new THREE.Mesh(new THREE.BoxGeometry(4.2, 2.8, 4), new THREE.MeshStandardMaterial({ color: 0x1f1f2a }));
      relay.position.set(12, 10 + r * 3.4, -24);
      elecGroup.add(relay);
    }
  }

  function buildGroundGrid() {
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(1200, 1200),
      new THREE.MeshStandardMaterial({ color: 0x050507, roughness: 0.9 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.5;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(300, 30, 0xff3b14, 0x181822);
    grid.position.y = 0;
    scene.add(grid);
  }



  // Focus Subsystem View
  window.focusSubsystem = function (key) {
    const view = CAMERA_VIEWS[key];
    if (!view) return;

    desiredCameraPos.copy(view.pos);
    desiredCameraTarget.copy(view.target);

    document.querySelectorAll('.focus-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById(`btn-focus-${key}`);
    if (btn) btn.classList.add('active');

    const badge = document.getElementById('view-badge');
    if (badge) badge.innerText = view.name;

    logTerminal("CAMERA", `Pan & focal lock: ${view.name}`, "info");
  };

  // Toggle X-Ray vs Solid Chassis
  window.toggleXRay = function () {
    isXRay = !isXRay;
    cutawayPanels.forEach(panel => {
      panel.material = isXRay ? matSmokedAcrylic : matObsidian;
    });
    const btn = document.getElementById('btn-xray');
    if (btn) btn.innerText = isXRay ? "X-RAY: ACTIVE" : "CHASSIS: SOLID";
    logTerminal("SURFACE", isXRay ? "Acrylic Cutaway View Active" : "Solid Chassis View Active", "ok");
  };

  // Place Drink Cup
  window.placeDrinkCup = function () {
    if (cupPresent) {
      logTerminal("WARN", "Cup is already seated on elevator coaster.", "alert");
      return;
    }
    cupPresent = true;
    elevatorGroup.userData.cupGroup.visible = true;
    cupLiquidMesh.scale.set(1, 0.001, 1);

    const btnPlace = document.getElementById('btn-place-cup');
    const btnDispense = document.getElementById('btn-dispense');
    if (btnPlace) btnPlace.disabled = true;
    if (btnDispense) btnDispense.disabled = false;

    updatePlcStep(2); // STEP 2: SAFETY_LATCH
    logTerminal("SENSOR", "IR Photocell: Vessel detected on platform.", "ok");
    logTerminal("HMI", `Ready to dispense [${currentRecipe.name}]`, "info");
  };

  // Recipe Selection
  window.selectRecipeHmi = function (name, activeBottleIds, blendColorHex, btnEl) {
    currentRecipe = {
      name: name,
      activeBottles: activeBottleIds,
      blendColor: parseInt(blendColorHex, 16),
      duration: 4.2
    };

    cupLiquidMesh.material.color.setHex(currentRecipe.blendColor);
    cupLiquidMesh.material.emissive.setHex(currentRecipe.blendColor);
    liquidStreamMesh.material.color.setHex(currentRecipe.blendColor);
    liquidStreamMesh.material.emissive.setHex(currentRecipe.blendColor);

    document.querySelectorAll('.hmi-drink-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    logTerminal("RECIPE", `Loaded [${name}]. Active lines: ${activeBottleIds.map(id => BOTTLE_CONFIGS[id].name).join(' + ')}`, "ok");
  };

  // Start Dispensing Sequence
  window.startDispenseCycle = function () {
    if (!cupPresent) {
      logTerminal("ERROR", "No cup detected on platform.", "alert");
      return;
    }
    if (cycleState !== STATE_IDLE && cycleState !== STATE_COMPLETE) return;

    cycleState = STATE_LOWERING;
    cycleProgress = 0;

    const btnDispense = document.getElementById('btn-dispense');
    if (btnDispense) btnDispense.disabled = true;

    updatePlcStep(3); // STEP 3: STEPPER_DRIVE_DOWN
    logTerminal("LIFT", "Stepper Motor: Driving T8 lead screw down to chamber limit...", "info");
  };

  // Update Dispense State Machine & Real Fluid Motion
  function updateDispenseCycle(delta) {
    if (cycleState === STATE_IDLE) return;

    if (cycleState === STATE_LOWERING) {
      cycleProgress += delta * 0.85;
      const t = Math.min(cycleProgress, 1);
      cupElevatorY = ELEVATOR_TOP_Y - (ELEVATOR_TOP_Y - ELEVATOR_BOTTOM_Y) * easeInOutQuad(t);
      elevatorGroup.position.y = cupElevatorY;

      if (cycleProgress >= 1) {
        cycleState = STATE_DISPENSING;
        cycleProgress = 0;
        liquidStreamMesh.visible = true;

        updatePlcStep(4); // STEP 4: CHECK_VALVE_PRIME
        setTimeout(() => updatePlcStep(5), 600); // STEP 5: PERISTALTIC_PWM_DISPENSE

        // Activate fluid pulses for active tubes
        fluidPulses.forEach(fp => {
          fp.active = currentRecipe.activeBottles.includes(fp.tubeIndex);
          fp.beads.forEach(b => b.mesh.visible = fp.active);
        });

        logTerminal("VALVE", "Inline check-valves opened under 24V differential pressure", "ok");
        logTerminal("PUMP", `Dispensing ingredients: ${currentRecipe.activeBottles.map(i => BOTTLE_CONFIGS[i].name).join(', ')}`, "info");
      }
    } else if (cycleState === STATE_DISPENSING) {
      cycleProgress += delta / currentRecipe.duration;
      const fillProgress = Math.min(cycleProgress, 1);

      // 1. Spin active peristaltic pump rollers
      currentRecipe.activeBottles.forEach(idx => {
        if (pumpRollers[idx]) {
          pumpRollers[idx].rotation.z += delta * 15;
        }
      });

      // 2. CRITICAL: DRAIN LIQUID LEVEL IN THE ACTIVE BOTTLES!
      currentRecipe.activeBottles.forEach(idx => {
        const bottle = bottles[idx];
        if (bottle) {
          // Drop liquid level by up to 25% per cocktail pour
          const targetDrain = 1.0 - fillProgress * 0.22;
          bottle.liquidMesh.scale.y = Math.max(0.1, targetDrain);
          bottle.liquidMesh.position.y = (bottle.initialHeight * targetDrain) / 2 + 0.5;

          // Update HMI gauge bar
          const gaugeFill = document.getElementById(`gauge-fill-${idx}`);
          if (gaugeFill) {
            gaugeFill.style.height = `${Math.round(targetDrain * 100)}%`;
          }
        }
      });

      // 3. VISIBLE FLUID IN TUBES: Animate fluid droplets advancing along active tubes!
      fluidPulses.forEach(fp => {
        if (fp.active) {
          const curve = tubeCurves[fp.tubeIndex];
          fp.beads.forEach(b => {
            b.offset = (b.offset + delta * 1.6) % 1.0;
            const pt = curve.getPoint(b.offset);
            b.mesh.position.copy(pt);
          });
        }
      });

      // 4. Fill cup with mixed liquid
      cupLiquidMesh.scale.set(1, fillProgress, 1);
      cupLiquidMesh.position.y = 1 + fillProgress * 6;

      if (cycleProgress >= 1) {
        cycleState = STATE_PURGING;
        cycleProgress = 0;
        liquidStreamMesh.visible = false;

        // Hide tube fluid beads
        fluidPulses.forEach(fp => {
          fp.active = false;
          fp.beads.forEach(b => b.mesh.visible = false);
        });

        updatePlcStep(6); // STEP 6: ANTI_DRIP_REVERSE_PULSE
        logTerminal("PUMP", "Peristaltic anti-drip reverse pulse executed.", "ok");

        setTimeout(() => {
          cycleState = STATE_RISING;
          cycleProgress = 0;
          updatePlcStep(7); // STEP 7: STEPPER_DRIVE_UP
          logTerminal("LIFT", "Elevating finished cocktail flush with tabletop...", "info");
        }, 500);
      }
    } else if (cycleState === STATE_RISING) {
      cycleProgress += delta * 0.85;
      const t = Math.min(cycleProgress, 1);
      cupElevatorY = ELEVATOR_BOTTOM_Y + (ELEVATOR_TOP_Y - ELEVATOR_BOTTOM_Y) * easeInOutQuad(t);
      elevatorGroup.position.y = cupElevatorY;

      if (cycleProgress >= 1) {
        cycleState = STATE_COMPLETE;
        updatePlcStep(8); // STEP 8: CYCLE_COMPLETE
        logTerminal("COMPLETE", `[${currentRecipe.name}] ready for pickup! Platform unlocked.`, "ok");

        const btnPlace = document.getElementById('btn-place-cup');
        if (btnPlace) {
          btnPlace.disabled = false;
          btnPlace.innerText = "RESET / NEW CUP";
          btnPlace.onclick = function () {
            cupPresent = false;
            elevatorGroup.userData.cupGroup.visible = false;
            cycleState = STATE_IDLE;
            btnPlace.innerText = "PLACE DRINK CUP";
            btnPlace.onclick = window.placeDrinkCup;
            updatePlcStep(1);
            logTerminal("RESET", "Cup removed. Platform re-zeroed.", "info");
          };
        }
      }
    }
  }

  function updatePlcStep(stepNum) {
    document.querySelectorAll('.plc-step-node').forEach(node => {
      const num = parseInt(node.getAttribute('data-step'), 10);
      node.classList.toggle('active', num === stepNum);
    });
  }

  function easeInOutQuad(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  function logTerminal(tag, message, statusClass) {
    const term = document.getElementById('telemetry-terminal');
    if (!term) return;

    const line = document.createElement('div');
    line.className = 'terminal-line';
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0');

    line.innerHTML = `
      <span class="time">[${timeStr}]</span>
      <span class="status-${statusClass}">[${tag}]</span>
      <span>${message}</span>
    `;

    term.appendChild(line);
    term.scrollTop = term.scrollHeight;
  }

  function onWindowResize() {
    const container = document.getElementById('three-viewport');
    if (!container || !renderer || !camera) return;
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  let clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();

    camera.position.lerp(desiredCameraPos, 0.045);
    if (controls) {
      controls.target.lerp(desiredCameraTarget, 0.045);
      controls.update();
    }

    updateDispenseCycle(delta);
    renderer.render(scene, camera);
  }

  window.initSimulation = init;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
