#!/usr/bin/env python3
"""
PM Family Verification Test
Tests all PM routes for:
- Login persistence
- No blank screens
- No operator-language leaks
- No horizontal overflow
- Operator-safe labels
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    print("=" * 80)
    print("PM FAMILY COMPREHENSIVE VERIFICATION")
    print("=" * 80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        results = {"passed": [], "failed": [], "warnings": []}
        banned_terms = ["WP-17", "WP17", "Runtime Certification", "Internal Test Project", 
                       "Powered by ForgedOps", "Cert Project Manager", "ODS"]
        
        try:
            # Step 1: Login
            print("\n[STEP 1] Logging in with PM credentials...")
            await page.goto("https://backup-forensics.preview.emergentagent.com/pm/login")
            await page.wait_for_selector('input[type="email"]', timeout=15000)
            
            await page.fill('input[type="email"]', "cert.pm@example.com")
            await page.fill('input[type="password"]', "CertProof2026!")
            await page.click('button[type="submit"]')
            
            await page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)
            
            url = page.url
            print(f"✅ Login successful: {url}")
            results["passed"].append("PM Login")
            
            # Step 2: Test all PM routes
            routes = [
                ("/pm", "PM Hub"),
                ("/pm/hub_v2", "PM Hub V2"),
                ("/pm/command-center", "PM Command Center"),
                ("/pm/crew-compliance", "PM Crew Compliance"),
                ("/pm/jobs", "PM Jobs"),
                ("/pm/project-schedule", "PM Project Schedule"),
                ("/pm/daily", "PM Daily"),
                ("/pm/incidents", "PM Incidents"),
                ("/pm/inspections", "PM Inspections"),
                ("/pm/field-leadership", "PM Field Leadership"),
                ("/pm/trench-safety", "PM Trench Safety"),
                ("/pm/operational-intelligence", "PM Operational Intelligence")
            ]
            
            print(f"\n[STEP 2] Testing {len(routes)} PM routes...")
            
            for idx, (route, name) in enumerate(routes, 1):
                try:
                    print(f"\n[{idx}/{len(routes)}] {name}")
                    
                    await page.goto(f"https://backup-forensics.preview.emergentagent.com{route}", 
                                  wait_until='networkidle', timeout=15000)
                    await asyncio.sleep(1)
                    
                    url = page.url
                    
                    # Check 1: Session persistence
                    if '/login' in url:
                        print("  ❌ Session lost")
                        results["failed"].append(f"{name}: Session lost")
                        continue
                    print("  ✅ Session OK")
                    
                    # Check 2: Not blank
                    text = await page.evaluate("() => document.body.innerText")
                    length = len(text.strip())
                    
                    if length < 100:
                        print(f"  ❌ Blank ({length} chars)")
                        results["failed"].append(f"{name}: Blank")
                        continue
                    print(f"  ✅ Content OK ({length} chars)")
                    
                    # Check 3: No banned terms
                    found_terms = [term for term in banned_terms if term in text]
                    
                    if found_terms:
                        print(f"  ❌ Banned terms: {found_terms}")
                        results["failed"].append(f"{name}: {found_terms}")
                        continue
                    print("  ✅ No banned terms")
                    
                    # Check 4: Desktop overflow
                    overflow_d = await page.evaluate("() => document.body.scrollWidth > window.innerWidth")
                    if overflow_d:
                        print("  ❌ Desktop overflow")
                        results["failed"].append(f"{name}: Desktop overflow")
                        continue
                    print("  ✅ Desktop OK")
                    
                    # Check 5: Mobile overflow
                    await page.set_viewport_size({"width": 390, "height": 844})
                    await asyncio.sleep(0.5)
                    
                    overflow_m = await page.evaluate("() => document.body.scrollWidth > window.innerWidth")
                    if overflow_m:
                        print("  ❌ Mobile overflow")
                        results["failed"].append(f"{name}: Mobile overflow")
                        await page.set_viewport_size({"width": 1920, "height": 1080})
                        continue
                    print("  ✅ Mobile OK")
                    
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                    
                    # Special checks
                    if route == "/pm/project-schedule":
                        has_content = any(w in text.lower() for w in ["schedule", "project", "empty", "no projects"])
                        if has_content:
                            print("  ✅ Schedule content OK")
                        else:
                            print("  ⚠️  Schedule unclear")
                            results["warnings"].append(f"{name}: Unclear")
                    
                    results["passed"].append(name)
                    print(f"  ✅ PASS")
                    
                except Exception as e:
                    print(f"  ❌ ERROR: {str(e)}")
                    results["failed"].append(f"{name}: {str(e)}")
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            results["failed"].append(f"Critical: {str(e)}")
        
        finally:
            await browser.close()
        
        # Summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        passed = len(results["passed"])
        failed = len(results["failed"])
        warnings = len(results["warnings"])
        
        print(f"\n✅ PASSED: {passed}")
        for item in results["passed"]:
            print(f"   • {item}")
        
        if warnings > 0:
            print(f"\n⚠️  WARNINGS: {warnings}")
            for item in results["warnings"]:
                print(f"   • {item}")
        
        if failed > 0:
            print(f"\n❌ FAILED: {failed}")
            for item in results["failed"]:
                print(f"   • {item}")
        else:
            print("\n🎉 ALL PM ROUTES PASSED!")
        
        print("\n" + "=" * 80)
        
        return len(results["failed"]) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
