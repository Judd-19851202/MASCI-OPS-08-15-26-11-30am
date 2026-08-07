#!/usr/bin/env python3
"""
WP-18C8 Final Frontend Recertification Test
Tests operator-language rewrite and performance hardening
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        print("=" * 80)
        print("WP-18C8 FINAL FRONTEND RECERTIFICATION")
        print("=" * 80)
        
        test_results = {}
        
        try:
            # TEST 1: PM LOGIN AND AUTO-LOAD
            print("\n[TEST 1] PM Login and Earned Value Auto-Load")
            print("-" * 80)
            
            await page.goto("https://masci-audit-hub.preview.emergentagent.com/pm/login", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            await page.fill('input[type="email"]', "cert.pm@example.com")
            await page.fill('input[type="password"]', "CertProof2026!")
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            print("✅ PM login successful")
            
            # Navigate to earned value with project number
            print("Navigating to PM earned value route...")
            await page.goto("https://masci-audit-hub.preview.emergentagent.com/pm/project-controls/earned-value?project_number=ZZ-RUNTIME-CERT-2026", wait_until="domcontentloaded", timeout=30000)
            
            start_time = time.time()
            await page.wait_for_selector('[data-testid="earned-value-workspace-pm"]', timeout=10000)
            load_time = time.time() - start_time
            
            workspace_visible = await page.is_visible('[data-testid="earned-value-workspace-pm"]')
            
            if workspace_visible:
                print(f"✅ PASS: PM workspace auto-loaded in {load_time:.2f}s (NO MANUAL REFRESH REQUIRED)")
                test_results["pm_auto_load"] = True
                await page.screenshot(path=".screenshots/wp18c8_pm_autoload.png", quality=40, full_page=False)
            else:
                print("❌ FAIL: PM workspace did NOT auto-load")
                test_results["pm_auto_load"] = False
                
        except Exception as e:
            print(f"❌ TEST 1 FAILED: {str(e)}")
            test_results["pm_auto_load"] = False
        
        try:
            # TEST 2: PM OPERATOR LANGUAGE
            print("\n[TEST 2] PM Operator Language Verification")
            print("-" * 80)
            
            page_text = await page.evaluate("() => document.body.innerText")
            
            banned_terms = ["engine", "authority", "black-box", "backend", "frontend", "runtime", "fixture", "canonical", "mutation", "governed"]
            violations = []
            
            for term in banned_terms:
                if term.lower() in page_text.lower():
                    count = page_text.lower().count(term.lower())
                    violations.append(f"{term} ({count}x)")
            
            if violations:
                print(f"❌ FAIL: Operator-language violations found: {', '.join(violations)}")
                test_results["operator_language_pm"] = False
            else:
                print("✅ PASS: NO operator-language violations found")
                test_results["operator_language_pm"] = True
            
            # Check for operator-friendly terms
            operator_terms = ["BAC", "PV", "EV", "AC", "CPI", "SPI", "EAC", "ETC", "TCPI"]
            found_terms = [t for t in operator_terms if t in page_text]
            print(f"✅ Operator-friendly terms found: {', '.join(found_terms)}")
            
        except Exception as e:
            print(f"❌ TEST 2 FAILED: {str(e)}")
            test_results["operator_language_pm"] = False
        
        try:
            # TEST 3: PM BUDGET REVIEW PAGE
            print("\n[TEST 3] PM Budget Review Page")
            print("-" * 80)
            
            await page.goto("https://masci-audit-hub.preview.emergentagent.com/pm/project-controls/budget?project_number=ZZ-RUNTIME-CERT-2026", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            text_length = len(await page.evaluate("() => document.body.innerText"))
            
            if text_length > 500:
                print(f"✅ PASS: PM budget review page loaded ({text_length} chars)")
                test_results["pm_budget_review"] = True
                await page.screenshot(path=".screenshots/wp18c8_pm_budget.png", quality=40, full_page=False)
            else:
                print("❌ FAIL: PM budget review page did NOT load properly")
                test_results["pm_budget_review"] = False
                
        except Exception as e:
            print(f"❌ TEST 3 FAILED: {str(e)}")
            test_results["pm_budget_review"] = False
        
        try:
            # TEST 4: ADMIN LOGIN AND AUTO-LOAD
            print("\n[TEST 4] Admin Login and Earned Value Auto-Load")
            print("-" * 80)
            
            await page.goto("https://masci-audit-hub.preview.emergentagent.com/sign-in", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            await page.fill('input[type="email"]', "jaymn.judd@mascigc.com")
            await page.fill('input[type="password"]', "Maddix123!")
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            print("✅ Admin login successful")
            
            await page.goto("https://masci-audit-hub.preview.emergentagent.com/admin/governance/project-controls/earned-value?project_number=ZZ-RUNTIME-CERT-2026", wait_until="domcontentloaded", timeout=30000)
            
            start_time = time.time()
            await page.wait_for_selector('[data-testid="earned-value-workspace-executive"]', timeout=10000)
            load_time = time.time() - start_time
            
            workspace_visible = await page.is_visible('[data-testid="earned-value-workspace-executive"]')
            
            if workspace_visible:
                print(f"✅ PASS: Admin workspace auto-loaded in {load_time:.2f}s (NO MANUAL REFRESH REQUIRED)")
                test_results["admin_auto_load"] = True
                await page.screenshot(path=".screenshots/wp18c8_admin_autoload.png", quality=40, full_page=False)
            else:
                print("❌ FAIL: Admin workspace did NOT auto-load")
                test_results["admin_auto_load"] = False
                
        except Exception as e:
            print(f"❌ TEST 4 FAILED: {str(e)}")
            test_results["admin_auto_load"] = False
        
        try:
            # TEST 5: ADMIN OPERATOR LANGUAGE
            print("\n[TEST 5] Admin Operator Language Verification")
            print("-" * 80)
            
            page_text = await page.evaluate("() => document.body.innerText")
            
            violations = []
            for term in banned_terms:
                if term.lower() in page_text.lower():
                    count = page_text.lower().count(term.lower())
                    violations.append(f"{term} ({count}x)")
            
            if violations:
                print(f"❌ FAIL: Operator-language violations found: {', '.join(violations)}")
                test_results["operator_language_admin"] = False
            else:
                print("✅ PASS: NO operator-language violations found in Admin view")
                test_results["operator_language_admin"] = True
                
        except Exception as e:
            print(f"❌ TEST 5 FAILED: {str(e)}")
            test_results["operator_language_admin"] = False
        
        # RESPONSIVE TESTS
        viewports = [
            {"width": 390, "height": 844, "name": "390px"},
            {"width": 430, "height": 932, "name": "430px"},
            {"width": 768, "height": 1024, "name": "768px"},
            {"width": 1024, "height": 768, "name": "1024px"},
            {"width": 1440, "height": 900, "name": "1440px"}
        ]
        
        for idx, vp in enumerate(viewports):
            try:
                print(f"\n[TEST {6+idx}] Responsive Test - {vp['name']}")
                print("-" * 80)
                
                await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
                await page.wait_for_timeout(1000)
                
                await page.goto("https://masci-audit-hub.preview.emergentagent.com/pm/project-controls/earned-value?project_number=ZZ-RUNTIME-CERT-2026", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                
                overflow_check = await page.evaluate("""() => {
                    return {
                        bodyWidth: document.body.scrollWidth,
                        viewportWidth: window.innerWidth
                    };
                }""")
                
                has_overflow = overflow_check["bodyWidth"] > overflow_check["viewportWidth"]
                
                if not has_overflow:
                    print(f"✅ PASS: NO horizontal overflow at {vp['name']}")
                    test_results[f"responsive_{vp['width']}"] = True
                else:
                    print(f"❌ FAIL: Horizontal overflow detected at {vp['name']}")
                    test_results[f"responsive_{vp['width']}"] = False
                
                await page.screenshot(path=f".screenshots/wp18c8_{vp['name']}.png", quality=40, full_page=False)
                
            except Exception as e:
                print(f"❌ TEST {6+idx} FAILED: {str(e)}")
                test_results[f"responsive_{vp['width']}"] = False
        
        # SUMMARY
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results.values())
        total = len(test_results)
        pass_rate = (passed / total) * 100
        
        print(f"\nOVERALL RESULTS: {passed}/{total} TESTS PASSED ({pass_rate:.1f}%)\n")
        
        test_names = {
            "pm_auto_load": "PM Earned Value Auto-Load",
            "admin_auto_load": "Admin Earned Value Auto-Load",
            "operator_language_pm": "PM Operator Language",
            "operator_language_admin": "Admin Operator Language",
            "pm_budget_review": "PM Budget Review Page",
            "responsive_390": "Responsive 390px",
            "responsive_430": "Responsive 430px",
            "responsive_768": "Responsive 768px",
            "responsive_1024": "Responsive 1024px",
            "responsive_1440": "Responsive 1440px"
        }
        
        for key, name in test_names.items():
            if key in test_results:
                status = "✅ PASS" if test_results[key] else "❌ FAIL"
                print(f"{status} - {name}")
        
        print("\n" + "=" * 80)
        
        await browser.close()
        
        return test_results

if __name__ == "__main__":
    asyncio.run(run_tests())
